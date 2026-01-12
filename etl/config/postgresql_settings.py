import os
from dataclasses import dataclass


@dataclass
class PostgresConfig:
    user: str = os.getenv("POSTGRES_USER", "admin")
    password: str = os.getenv("POSTGRES_PASSWORD", "admin0000")
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = os.getenv("POSTGRES_PORT", 5432)
    dbname: str = os.getenv("POSTGRES_DBNAME", "audio_midi")

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"


postgres_config = PostgresConfig()
