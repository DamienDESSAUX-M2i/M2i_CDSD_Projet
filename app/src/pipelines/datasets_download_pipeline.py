import logging
from dataclasses import dataclass
from pathlib import Path

from settings import (
    DATASETS_DOWNLOADER_SETTINGS,
    GUITAR_SET_CONFIG,
    IDMT_SMT_GUITAR_CONFIG,
)
from settings.dataset_settings import DatasetSettings

from src.downloaders import DatasetDownloader
from src.extractors import ZipExtractor
from src.utils import Statistics


@dataclass
class DatasetsDownloadPipelineStatistics(Statistics):
    """Statistics container for dataset download and extraction pipeline.

    Attributes:
        dataset_download: Number of successful dataset downloads.
        dataset_download_error: Number of failed dataset download attempts.
        dataset_unzip: Number of successful extraction operations.
        dataset_unzip_error: Number of failed extraction operations.
    """

    dataset_download: int = 0
    dataset_download_error: int = 0
    dataset_unzip: int = 0
    dataset_unzip_error: int = 0


class DatasetsDownloadPipeline:
    """Pipeline responsible for downloading and extracting datasets."""

    def __init__(
        self,
        logger: logging.Logger,
        guitar_set: bool,
        idmt_smt_guitar: bool,
        base_directory: Path = Path("./app/data/raw").resolve(),
    ) -> None:
        """Initialize the datasets download pipeline.

        Args:
            logger: Logger instance.
            guitar_set: Whether to process the GuitarSet dataset.
            idmt_smt_guitar: Whether to process the IDMT-SMT-Guitar dataset.
            base_directory: Path of the data directory.
        """

        self.logger = logger
        self.guitar_set = guitar_set
        self.idmt_smt_guitar = idmt_smt_guitar
        self.base_directory = base_directory

        self.downloader = DatasetDownloader(
            logger=self.logger,
            settings=DATASETS_DOWNLOADER_SETTINGS,
        )
        self.extractor = ZipExtractor(logger=self.logger)
        self.statistics = DatasetsDownloadPipelineStatistics()

    def run(self) -> None:
        """Execute the dataset download and extraction pipeline.

        This method orchestrates the full workflow:
        - downloads datasets
        - extracts downloaded archives
        - tracks success and error statistics

        Raises:
            RuntimeError: If an unrecoverable error occurs during execution.
        """
        try:
            self.logger.info("Download datasets pipeline start...")

            if self.guitar_set:
                self.logger.info("GuitarSet downloading ...")
                self._process_dataset(GUITAR_SET_CONFIG)

            if self.idmt_smt_guitar:
                self.logger.info("IDMT-SMT-Guitar downloading ...")
                self._process_dataset(IDMT_SMT_GUITAR_CONFIG)

            self.logger.info(f"Pipeline completed: {self.statistics.to_string()}")

        except Exception as exception:
            self.logger.exception("Download pipeline failed")
            raise RuntimeError("Download pipeline failed") from exception

    def _process_dataset(self, dataset_settings: DatasetSettings) -> None:
        """Process a dataset: download and extract all its archives.

        Args:
            dataset_settings: Dataset configuration containing URLs, archive names,
                and extraction directory information.
        """
        dataset_dir = self.base_directory / dataset_settings.extract_dir_name

        for url, archive_name in zip(
            dataset_settings.urls, dataset_settings.archive_names
        ):
            archive_path = self.base_directory / archive_name
            extract_path = (dataset_dir / archive_name).with_suffix("")

            self._download(url, archive_path, dataset_settings.name)
            self._extract(archive_path, extract_path, dataset_settings.name)

    def _download(self, url: str, archive_path: Path, dataset_name: str) -> None:
        """Download a dataset archive if it does not already exist.

        Args:
            url: Source URL of the dataset archive.
            archive_path: Local filesystem path where the archive will be stored.
            dataset_name: Name of the dataset for logging purposes.

        Raises:
            Exception: Propagates any exception raised by the downloader.
        """
        try:
            if archive_path.exists():
                self.logger.info(
                    f"Skipping download, file exists: archive_path={archive_path}"
                )
                return

            self.downloader.download(url, archive_path)
            self.statistics.dataset_download += 1

        except Exception:
            self.statistics.dataset_download_error += 1
            self.logger.exception(
                f"Dataset download failed: dataset={dataset_name}, url={url}"
            )
            raise

    def _extract(
        self, archive_path: Path, extract_path: Path, dataset_name: str
    ) -> None:
        """Extract a dataset archive if not already extracted.

        Args:
            archive_path: Path to the archive file.
            extract_path: Target directory for extracted content.
            dataset_name: Name of the dataset for logging purposes.

        Raises:
            Exception: Propagates any exception raised during extraction.
        """
        try:
            if extract_path.exists() and any(extract_path.iterdir()):
                self.logger.info(
                    f"Skipping unzip, directory exists: extract_path={extract_path}"
                )
                return

            self.extractor.extract(archive_path, extract_path)
            self.statistics.dataset_unzip += 1

        except Exception:
            self.statistics.dataset_unzip_error += 1
            self.logger.exception(
                f"Dataset unzip failed: dataset={dataset_name}, archive={archive_path}"
            )
            raise
