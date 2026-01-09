import os

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class PostgresConfig(BaseSettings):
    user: str = os.getenv("POSTGRES_USER")
    password: str = os.getenv("POSTGRES_PASSWORD")
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = os.getenv("POSTGRES_PORT", 5432)
    dbname: str = os.getenv("POSTGRES_DBNAME")

    @property
    def connection_string(self) -> PostgresDsn:
        return PostgresDsn(
            f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
        )


postgres_config = PostgresConfig()
