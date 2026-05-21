from __future__ import annotations

import logging
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from settings.dataset_downloader_settings import DatasetsDownloaderSettings
from tqdm import tqdm
from urllib3 import Retry

from .abstract_dataset_downloader import AbstractDatasetDownloader


class DatasetDownloader(AbstractDatasetDownloader):
    """
    HTTP dataset downloader with retry and resume support.
    """

    def __init__(
        self,
        logger: logging.Logger,
        settings: DatasetsDownloaderSettings,
    ) -> None:
        """
        Initialize the dataset downloader.

        Args:
            logger: Application logger.
            config: Download configuration.
        """
        super().__init__(logger)

        self.settings = settings
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        """
        Build a configured HTTP session.

        Returns:
            Configured requests session.
        """
        retry = Retry(
            total=self.settings.retry_total,
            backoff_factor=self.settings.retry_backoff_factor,
            status_forcelist=self.settings.retry_status_forcelist,
            allowed_methods=self.settings.retry_allowed_methods,
        )

        adapter = HTTPAdapter(max_retries=retry)

        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _build_headers(self) -> dict[str, str]:
        """
        Build request headers.

        Returns:
            HTTP headers dictionary.
        """
        headers = {
            "User-Agent": self.settings.user_agent,
        }

        if self.settings.token is not None:
            headers["Authorization"] = f"Bearer {self.settings.token}"

        return headers

    def download(
        self,
        url: str,
        output_path: Path,
    ) -> None:
        """
        Download a dataset archive.

        Args:
            url: Remote archive URL.
            output_path: Local destination path.

        Raises:
            FileExistsError: If output file already exists.
            RuntimeError: If download permanently fails.
        """
        if output_path.exists():
            raise FileExistsError(f"Output file already exists: {output_path}")

        tmp_path = output_path.with_suffix(f"{output_path.suffix}.part")

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        headers = self._build_headers()

        for attempt in range(1, self.settings.max_retry_attempts + 1):
            try:
                self._download_once(
                    url=url,
                    output_path=output_path,
                    tmp_path=tmp_path,
                    headers=headers.copy(),
                )

                return

            except requests.RequestException as exception:
                self.logger.warning(
                    f"Download attempt failed: attempt={attempt} url={url} error={exception}",
                )

                if attempt >= self.settings.max_retry_attempts:
                    raise RuntimeError(f"Download failed: {url}") from exception

                time.sleep(self.settings.backoff_factor**attempt)

    def _download_once(
        self,
        *,
        url: str,
        output_path: Path,
        tmp_path: Path,
        headers: dict[str, str],
    ) -> None:
        """
        Execute a single dataset download attempt.

        This method supports resumable downloads using HTTP Range headers
        when a partial temporary file already exists.

        Downloaded content is first written into a temporary `.part` file
        before being atomically renamed to the final output path.

        Args:
            url: Remote dataset archive URL.
            output_path: Final destination path.
            tmp_path: Temporary partial download path.
            headers: HTTP request headers.

        Raises:
            RuntimeError: If the download is empty or resume is unsupported.
            requests.RequestException: If the HTTP request fails.
        """
        existing_size = tmp_path.stat().st_size if tmp_path.exists() else 0

        request_headers = headers.copy()

        if existing_size > 0:
            request_headers["Range"] = f"bytes={existing_size}-"

            self.logger.info(
                f"Resuming partial download: url={url} existing_size={existing_size}"
            )

        with self.session.get(
            url,
            stream=True,
            headers=request_headers,
            timeout=self.settings.timeout_seconds,
        ) as response:
            self.logger.debug(
                f"HTTP response received: url={url} status_code={response.status_code}"
            )

            if existing_size > 0 and response.status_code != requests.codes.partial:
                self.logger.warning(
                    f"Server does not support resumable downloads: url={url}"
                )

                tmp_path.unlink(missing_ok=True)

                raise RuntimeError("Server does not support resume")

            response.raise_for_status()

            content_length = int(response.headers.get("Content-Length", 0))

            total_size = existing_size + content_length

            file_mode = "ab" if existing_size > 0 else "wb"

            with (
                tmp_path.open(file_mode) as file_handle,
                tqdm(
                    total=total_size,
                    initial=existing_size,
                    unit="B",
                    unit_scale=True,
                    desc=output_path.name,
                    colour="green",
                ) as progress_bar,
            ):
                for chunk in response.iter_content(
                    chunk_size=self.settings.chunk_size,
                ):
                    if not chunk:
                        continue

                    file_handle.write(chunk)
                    progress_bar.update(len(chunk))

        if not tmp_path.exists() or tmp_path.stat().st_size == 0:
            raise RuntimeError(f"Downloaded file is empty: {url}")

        tmp_path.rename(output_path)

        self.logger.info(f"Download completed successfully: output_path={output_path}")
