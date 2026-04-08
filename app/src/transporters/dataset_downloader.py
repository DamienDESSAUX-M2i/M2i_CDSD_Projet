import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3 import Retry

from src.transporters import AbstractTransporter


class DatasetDownloader(AbstractTransporter):
    """Downloader for datasets."""

    def __init__(
        self,
        chunk_size: int = 8192,
        timeout: int = 30,
        max_retry_attempts: int = 5,
        backoff_factor: float = 1.5,
        retry_total: int = 3,
        retry_backoff_factor: float = 1,
        retry_status_forcelist: tuple[int, ...] = (500, 502, 503, 504),
        retry_allowed_methods: tuple[str, ...] = ("GET",),
        token: str | None = None,
        user_agent: str = "DatasetDownloader/1.0",
    ):
        """
        Initializes the DatasetDownloader.

        Args:
            chunk_size (int): Size of chunks to read from the response stream.
            timeout (int): Timeout in seconds for HTTP requests.
            max_retry_attempts (int): Number of global retry attempts for the full download.
            backoff_factor (float): Exponential backoff factor for global retry delays.
            retry_total (int): Total number of HTTP-level retries for transient errors.
            retry_backoff_factor (float): Backoff factor for HTTP-level retries.
            retry_status_forcelist (tuple[int, ...]): HTTP status codes that trigger a retry.
            retry_allowed_methods (tuple[str, ...]): HTTP methods that are retried.
            token (str, optional): Bearer token for authorization headers.
            user_agent (str): Default User-Agent string to use for requests.
        """
        super().__init__()
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.max_retry_attempts = max_retry_attempts
        self.backoff_factor = backoff_factor
        self.default_retry_total = retry_total
        self.default_retry_backoff_factor = retry_backoff_factor
        self.default_retry_status_forcelist = retry_status_forcelist
        self.default_retry_allowed_methods = retry_allowed_methods
        self.default_token = token
        self.default_user_agent = user_agent
        self.session = self._build_session(
            retry_total=self.default_retry_total,
            retry_backoff_factor=self.default_retry_backoff_factor,
            status_forcelist=self.default_retry_status_forcelist,
            allowed_methods=self.default_retry_allowed_methods,
        )

        self.logger.debug(
            f"DatasetDownloader initialized, chunk_size={chunk_size}, timeout={timeout}, max_retry_attempts={max_retry_attempts}"
        )

    def _build_session(
        self,
        retry_total: int,
        retry_backoff_factor: float,
        status_forcelist: tuple[int, ...],
        allowed_methods: tuple[str, ...],
    ) -> requests.Session:
        """
        Builds a requests.Session with urllib3 Retry configuration.

        Args:
            retry_total (int): Total number of HTTP-level retries for transient errors.
            retry_backoff_factor (float): Backoff factor for HTTP-level retries.
            status_forcelist (tuple[int, ...]): HTTP status codes that trigger a retry.
            allowed_methods (tuple[str, ...]): HTTP methods that are retried.

        Returns:
            requests.Session: Configured session with retry logic.
        """
        self.logger.debug(
            f"Building HTTP session, retry_total={retry_total}, retry_backoff_factor={retry_backoff_factor}, status_forcelist={status_forcelist}"
        )

        retry = Retry(
            total=retry_total,
            backoff_factor=retry_backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=allowed_methods,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def download(
        self,
        url: str,
        output_path: Path,
        *,
        max_retry_attempts: int | None = None,
        backoff_factor: float | None = None,
        retry_total: int | None = None,
        retry_backoff_factor: float | None = None,
        retry_status_forcelist: tuple[int, ...] | None = None,
        retry_allowed_methods: tuple[str, ...] | None = None,
        token: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Downloads a file from a URL with resume support, configurable retry strategy,
        authentication headers, and progress tracking.

        The method supports partial download resumption using HTTP Range headers and
        performs global retry attempts in case of failures (network issues, timeouts,
        interrupted streams). HTTP-level retries are handled via urllib3 Retry, while
        higher-level retries wrap the full download process.

        Args:
            url (str): URL of the file to download.
            output_path (Path): Destination path where the file will be saved.
            max_retry_attempts (int, optional): Overrides the default number of global
                retry attempts for the full download process.
            backoff_factor (float, optional): Overrides the exponential backoff factor
                applied between global retry attempts.
            retry_total (int, optional): Overrides the total number of HTTP-level retries
                for transient errors.
            retry_backoff_factor (float, optional): Overrides the backoff factor used by
                urllib3 Retry for HTTP-level retries.
            retry_status_forcelist (tuple[int, ...], optional): Overrides the set of HTTP
                status codes that trigger a retry (e.g. 500, 502, 503, 504).
            retry_allowed_methods (tuple[str, ...], optional): Overrides the HTTP methods
                eligible for retry (typically ("GET",)).
            token (str, optional): Bearer token used for authentication. If provided,
                it is added to the Authorization header.
            user_agent (str, optional): Custom User-Agent header value for the request.

        Raises:
            RuntimeError: If the downloaded file is empty or if resume is not supported
                when attempting to continue a partial download.
            requests.RequestException: If an HTTP error occurs during the request.
            Exception: If the maximum number of retry attempts is reached without success.
        """
        if output_path.exists():
            self.logger.info(
                f"File already exists: output_path={str(output_path)}",
            )
            raise

        self.logger.info(
            f"Starting download: url={url}, output_path={str(output_path)}",
        )

        tmp_path = output_path.with_suffix(output_path.suffix + ".part")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        max_retry_attempts = max_retry_attempts or self.max_retry_attempts
        backoff_factor = backoff_factor or self.backoff_factor
        token = token or self.default_token
        user_agent = user_agent or self.default_user_agent

        if any(
            param is not None
            for param in (
                retry_total,
                retry_backoff_factor,
                retry_status_forcelist,
                retry_allowed_methods,
            )
        ):
            self.logger.debug("Using custom retry configuration")

            session = self._build_session(
                retry_total=retry_total or self.default_retry_total,
                retry_backoff_factor=retry_backoff_factor
                or self.default_retry_backoff_factor,
                status_forcelist=retry_status_forcelist
                or self.default_retry_status_forcelist,
                allowed_methods=retry_allowed_methods
                or self.default_retry_allowed_methods,
            )
        else:
            session = self.session

        headers = {"User-Agent": user_agent}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        for attempt in range(1, max_retry_attempts + 1):
            try:
                self.logger.info(f"Download attempt: attempt={attempt}, url={url}")

                self._download_once(
                    url=url,
                    output_path=output_path,
                    tmp_path=tmp_path,
                    session=session,
                    headers=headers,
                )

                self.logger.info(f"Download complete: path={str(output_path)}")
                return
            except Exception as exception:
                self.logger.warning(
                    f"Download attempt failed: attempt={attempt}, error={str(exception)}, url={url}"
                )

                if attempt == max_retry_attempts:
                    self.logger.error(
                        f"Max retries reached: url={url}",
                    )
                    raise

                sleep_time = backoff_factor**attempt
                self.logger.debug(f"Retrying after backoff: sleep_time={sleep_time}")
                time.sleep(sleep_time)

    def _download_once(
        self,
        url: str,
        output_path: Path,
        tmp_path: Path,
        session: requests.Session,
        headers: dict[str, str],
    ) -> None:
        existing_size = tmp_path.stat().st_size if tmp_path.exists() else 0

        if existing_size > 0:
            headers["Range"] = f"bytes={existing_size}-"
            self.logger.info(f"Resuming download: url{url}, bytes={existing_size}")

        with session.get(
            url=url,
            stream=True,
            headers=headers,
            timeout=self.timeout,
        ) as response:
            self.logger.debug(
                f"HTTP response received: status_code={response.status_code}, url={url}"
            )

            if existing_size > 0 and response.status_code != 206:
                self.logger.warning(
                    f"Server does not support resume, restarting download: url={url}"
                )
                tmp_path.unlink(missing_ok=True)
                raise RuntimeError("Resume not supported")

            response.raise_for_status()

            total_size = int(response.headers.get("Content-Length", 0)) + existing_size
            mode = "ab" if existing_size > 0 else "wb"

            self.logger.debug(
                f"Starting stream download: total_size={total_size}, mode={mode}"
            )

            with (
                tmp_path.open(mode) as f,
                tqdm(
                    total=total_size,
                    initial=existing_size,
                    unit="B",
                    unit_scale=True,
                    desc=output_path.name,
                    ascii=True,
                ) as pbar,
            ):
                for chunk in response.iter_content(self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        if not tmp_path.exists() or tmp_path.stat().st_size == 0:
            self.logger.error(f"Empty download detected: url={url}")
            raise RuntimeError("Empty download")

        tmp_path.rename(output_path)

        self.logger.debug(
            f"Temporary file renamed to final output: output_path={str(output_path)}"
        )
