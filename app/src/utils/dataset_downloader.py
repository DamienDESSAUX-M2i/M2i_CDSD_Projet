import logging
import zipfile
from pathlib import Path

import requests
from config import Dataset, datasets_config
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tqdm import tqdm

from src.utils.logger import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


USER_AGENT = "dataset-downloader/1.0"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(RuntimeError),
    reraise=True,
)
def _download_file(url: str, output_path: Path) -> None:
    """Download a file from a URL.

    The function skips the download if the target file already exists.
    It streams the file to disk to avoid loading it entirely into memory,
    and displays a progress bar when the content length is available.

    Args:
        url (str): The URL of the file to download.
        output_path (Path): The local filesystem path where the file will be saved.

    Raises:
        RuntimeError: If the download fails due to network issues, HTTP errors, or if the downloaded file is empty.
    """

    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info(f"File already exists, skipping: output_path={output_path}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading url={url}")

    headers = {"User-Agent": USER_AGENT}

    try:
        with requests.get(url, stream=True, timeout=30, headers=headers) as response:
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))

            with (
                output_path.open("wb") as f,
                tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    desc=output_path.name,
                    colour="green",
                ) as progress_bar,
            ):
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))

    except requests.RequestException as exception:
        logger.warning(f"Download failed, will retry: url={url}")
        raise RuntimeError(f"Download failed: {url}") from exception

    if output_path.stat().st_size == 0:
        raise RuntimeError("Downloaded file is empty")

    logger.info(f"Downloaded to output_path={output_path}")


def _safe_extract(zip_path: Path, output_dir: Path) -> None:
    """Extract a ZIP archive into a directory.

    This function prevents Zip Slip vulnerabilities by validating that
    all extracted files remain within the target directory. Extraction
    is skipped if the output directory already exists and is not empty.

    Args:
        zip_path (Path): Path to the ZIP archive to extract.
        output_dir (Path): Directory where the archive will be extracted.

    Raises:
        RuntimeError: If the archive contains unsafe paths or if extraction fails.
    """

    if output_dir.exists() and any(output_dir.iterdir()):
        logger.info(f"Already extracted, skipping: output_dir={output_dir}")
        return

    logger.info(f"Extracting zip_path={zip_path}")

    output_dir_resolved = output_dir.resolve()

    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.infolist():
            member_path = (output_dir / member.filename).resolve()

            if not member_path.is_relative_to(output_dir_resolved):
                raise RuntimeError(f"Unsafe zip file: {member.filename}")

        z.extractall(output_dir)

    logger.info(f"Extracted to output_dir={output_dir}")


def download_and_extract_dataset(dataset: Dataset, base_dir: Path) -> None:
    """Download and extract a dataset based on its configuration.

    This function retrieves dataset metadata from a central configuration,
    downloads the archive if needed, and extracts it into the appropriate
    directory.

    Args:
        dataset (Dataset): Dataset identifier (enum).
        base_dir (Path): Base directory where the dataset will be stored.

    Raises:
        KeyError: If the dataset is not configured.
        RuntimeError: If download or extraction fails.
    """

    config = datasets_config[dataset]

    zip_path = base_dir / config.archive_name
    extract_dir = base_dir / config.extract_dir

    for url in config.url:
        _download_file(url, zip_path)
        _safe_extract(zip_path, extract_dir)
