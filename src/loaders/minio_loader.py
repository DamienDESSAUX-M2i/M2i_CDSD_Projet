from pathlib import Path

from src.loaders.abstract_loader import AbstractLoader
from src.utils import minio


class MinioLoader(AbstractLoader):
    """Loader for MinIO."""

    def load(self, bucket_name: str, object_name: str, file_path: Path) -> None:
        """Load data to MinIO.

        Args:
            bucket_name (str): Name of the bucket containing the file to download.
            object_name (str): Name of the object to download.
            file_path (Path): Path to the downloaded file.
        """
        try:
            self.logger.info("Attempting to connect to the MinIO service.")
            client = minio.get_client()
            self.logger.info("Connecting to the MinIO service.")
            self.logger.info(f"Attempting to load the file : {file_path}.")
            client.fput_object(
                bucket_name=bucket_name, object_name=object_name, file_path=file_path
            )
            self.logger.info(f"Object loaded : {'/'.join([bucket_name, object_name])}")
        except Exception as e:
            self.logger.error(f"Error MinIO loader : {e}.")
            raise
