from dataclasses import dataclass
from pathlib import Path

from config import (
    download_datasets_pipeline_config,
    guitar_set_config,
    idmt_smt_guitar_config,
)

from src.extractors import ZipExtractor
from src.pipelines import AbstractPipeline
from src.transporters import DatasetDownloader
from src.utils import Statistics


@dataclass
class DownloadDatasetsPipelineStatistics(Statistics):
    dataset_download: int = 0
    dataset_download_error: int = 0
    dataset_unzip: int = 0
    dataset_unzip_error: int = 0


class DownloadDatasetsPipeline(AbstractPipeline):
    """Pipeline for download and extract datasets."""

    def __init__(
        self,
        guitarset: bool = True,
        idmt_smt_guitar: bool = True,
    ):
        super().__init__()
        self.guitarset = guitarset
        self.idmt_smt_guitar = idmt_smt_guitar
        self.base_dir = Path(download_datasets_pipeline_config.base_dir)
        self.downloader = DatasetDownloader(
            chunk_size=download_datasets_pipeline_config.chunk_size,
            timeout=download_datasets_pipeline_config.timeout,
            max_retry_attempts=download_datasets_pipeline_config.max_retry_attempts,
            backoff_factor=download_datasets_pipeline_config.backoff_factor,
            retry_total=download_datasets_pipeline_config.retry_total,
            retry_backoff_factor=download_datasets_pipeline_config.retry_backoff_factor,
            retry_status_forcelist=download_datasets_pipeline_config.retry_status_forcelist,
            retry_allowed_methods=download_datasets_pipeline_config.retry_allowed_methods,
            token=download_datasets_pipeline_config.token,
            user_agent=download_datasets_pipeline_config.user_agent,
        )
        self.extractor = ZipExtractor()
        self.statistics = DownloadDatasetsPipelineStatistics()

    def run(self) -> None:
        """Run pipeline.

        Raises:
            RuntimeError: If pipeline failed.
        """
        try:
            self.logger.info("Download datasets pipeline start...")

            if self.guitarset:
                self.logger.info("GuitarSet downloading ...")
                self._download_and_extract_guitarset()
                self.logger.info("GuitarSet download completed")

            if self.idmt_smt_guitar:
                self.logger.info("IDMT-SMT-Guitar downloading ...")
                self._download_and_extract_idmt_smt_guitar()
                self.logger.info("IDMT-SMT-Guitar download completed")

            self.logger.info(
                f"Download datasets pipeline completed: {self.statistics.to_string()}"
            )
        except Exception as exception:
            self.logger.info(f"Ingestion pipeline has failed: {exception}")
            raise RuntimeError("Ingestion pipeline has failed") from exception

    def _download_and_extract_guitarset(self) -> None:
        self.logger.info(f"Dataset state, dataset={guitar_set_config.name}")

        extract_dir_path = self.base_dir / guitar_set_config.extract_dir
        for url, archive_name in zip(
            guitar_set_config.urls, guitar_set_config.archive_names
        ):
            try:
                archive_path = self.base_dir / archive_name
                if archive_path.exists():
                    self.logger.info(
                        f"Skipping download, file already exists: archive_path={archive_path}"
                    )
                else:
                    self.downloader.download(url, archive_path)
                    self.statistics.dataset_download += 1

            except Exception:
                self.logger.exception(
                    f"Dataset download failed: dataset={guitar_set_config.name}, url={url}"
                )
                self.statistics.dataset_download_error += 1
                raise

            try:
                extract_path = (extract_dir_path / archive_name).with_suffix("")
                if extract_path.exists() and any(extract_path.iterdir()):
                    self.logger.info(
                        f"Skipping unzip, directory already exists, extract_path={extract_path}"
                    )
                else:
                    self.extractor.extract_zip(archive_path, extract_path)
                    self.statistics.dataset_unzip += 1

            except Exception:
                self.logger.exception(
                    f"Dataset unzip failed: dataset={guitar_set_config.name}, archive_path={archive_path}"
                )
                self.statistics.dataset_unzip_error += 1
                raise

    def _download_and_extract_idmt_smt_guitar(self) -> None:
        self.logger.info(f"Dataset state, dataset={idmt_smt_guitar_config.name}")

        extract_dir_path = self.base_dir / idmt_smt_guitar_config.extract_dir
        for url, archive_name in zip(
            idmt_smt_guitar_config.urls, idmt_smt_guitar_config.archive_names
        ):
            try:
                archive_path = self.base_dir / archive_name
                if archive_path.exists():
                    self.logger.info(
                        f"Skipping download, file already exists: archive_path={archive_path}"
                    )
                else:
                    self.downloader.download(url, archive_path)
                    self.statistics.dataset_download += 1

            except Exception:
                self.logger.exception(
                    f"Dataset download failed: dataset={guitar_set_config.name}, url={url}"
                )
                self.statistics.dataset_download_error += 1
                raise

            try:
                extract_path = extract_dir_path
                if extract_path.exists() and any(extract_path.iterdir()):
                    self.logger.info(
                        f"Skipping unzip, directory already exists, extract_path={extract_path}"
                    )
                else:
                    self.extractor.extract_zip(archive_path, extract_path)
                    self.statistics.dataset_unzip += 1

            except Exception:
                self.logger.exception(
                    f"Dataset unzip failed: dataset={guitar_set_config.name}, archive_path={archive_path}"
                )
                self.statistics.dataset_unzip_error += 1
                raise
