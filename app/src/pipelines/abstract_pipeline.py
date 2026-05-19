import logging
from abc import ABC, abstractmethod

from src.storages import MinIOStorage, MongoStorage, PostgresStorage


class AbstractPipeline(ABC):
    """Base class for data pipelines."""

    def __init__(
        self,
        logger: logging.Logger,
    ):
        self.logger = logger
        self.minio_storage = MinIOStorage(logger=self.logger)
        self.mongo_storage = MongoStorage(logger=self.logger)
        self.postgres_storage = PostgresStorage(logger=self.logger)

    @abstractmethod
    def run(self) -> None:
        """Execute the pipeline."""

        raise NotImplementedError

    def close(self):
        """Close pipeline properly."""

        self.mongo_storage.close()
        self.postgres_storage.close()
