import os
from pathlib import Path
from typing import Tuple, Type

from pydantic import AnyHttpUrl, BaseModel, PositiveInt, PostgresDsn
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

ETL_SETTINGS_PATH = Path("/app/config/etl_config.yaml")


class MinIOConfig(BaseSettings):
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_ENDPOINT: str
    BUCKET_BRONZE: str
    BUCKET_SILVER: str
    BUCKET_GOLD: str


minio_config = MinIOConfig(
    MINIO_ROOT_USER=os.getenv("MINIO_ROOT_USER"),
    MINIO_ROOT_PASSWORD=os.getenv("MINIO_ROOT_PASSWORD"),
    MINIO_ENDPOINT=os.getenv("MINIO_ENDPOINT"),
    BUCKET_BRONZE=os.getenv("BUCKET_BRONZE", "bronze"),
    BUCKET_SILVER=os.getenv("BUCKET_SILVER", "silver"),
    BUCKET_GOLD=os.getenv("BUCKET_GOLD", "gold"),
)


class PostgreSQLConfig(BaseSettings):
    user: str
    password: str
    host: str
    port: int
    dbname: str

    @property
    def connection_string(self) -> PostgresDsn:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"


postgresql_config = PostgreSQLConfig(
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", 5432),
    dbname=os.getenv("POSTGRES_DB"),
)


class APIModel(BaseModel):
    base_url: AnyHttpUrl
    endpoint: str
    timeout: PositiveInt = 30
    retry: PositiveInt = 3


class ETLConfig(BaseSettings):
    model_config = SettingsConfigDict(
        yaml_file=ETL_SETTINGS_PATH,
        yaml_file_encoding="utf-8",
    )
    api: APIModel

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        yaml_settings = YamlConfigSettingsSource(settings_cls)
        return (yaml_settings,)


etl_config = ETLConfig()
