import os

from pydantic import MongoDsn
from pydantic_settings import BaseSettings


class MongoConfig(BaseSettings):
    user: str = os.getenv("MONGO_USER")
    password: str = os.getenv("MONGO_PASSWORD")
    host: str = os.getenv("MONGO_HOST", "localhost")
    port: int = os.getenv("MONGO_PORT", 27017)
    dbname: str = os.getenv("MONGO_DBNAME")

    @property
    def connection_string(self) -> MongoDsn:
        return MongoDsn(
            f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/"
        )


mongo_config = MongoConfig()
