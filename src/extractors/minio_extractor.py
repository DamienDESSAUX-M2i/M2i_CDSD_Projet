from pathlib import Path

from src.extractors.abstract_extractor import AbstractExtractor
from src.utils import minio


class MinioExtractor(AbstractExtractor):
    """Extractor for MinIO."""

    def extract(self, bucket_name: str, object_name: str, file_path: Path) -> None:
        """Extract data from MinIO.

        Args:
            bucket_name (str): Name of the bucket containing the file to download.
            object_name (str): Name of the object to download.
            file_path (Path): Path to the downloaded file.
        """
        try:
            self.logger.info("Attempting to connect to the MinIO service.")
            client = minio.client()
            self.logger.info("Connecting to the MinIO service.")
            self.logger.info(
                f"Attempting to download the object : {'/'.join([bucket_name, object_name])}."
            )
            client.fget_object(
                bucket_name=bucket_name, object_name=object_name, file_path=file_path
            )
            self.logger.info(f"File downloaded : {file_path}.")
        except Exception as e:
            self.logger.error(f" Error MinIO extractor: {e}.")
