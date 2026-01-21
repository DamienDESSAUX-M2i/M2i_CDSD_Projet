import logging
from abc import ABC, abstractmethod

from src.storages import MinIOStorage, MongoStorage, PostgresStorage
from src.utils import LOGGER_NAME


class AbstractPipeline(ABC):
    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.minio_storage = MinIOStorage()
        self.mongo_storage = MongoStorage()
        self.postgres_storage = PostgresStorage()

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError

    def close(self):
        """Close pipeline properly."""
        self.mongo_storage.close()
        self.postgres_storage.close()
