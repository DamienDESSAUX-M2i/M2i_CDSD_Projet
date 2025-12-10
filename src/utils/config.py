from pathlib import Path
from typing import Tuple, Type

from pydantic import AnyHttpUrl, BaseModel, PositiveInt, SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

MINIO_ENV_PATH = Path("./config/minio.env")
ETL_SETTINGS_PATH = Path("./config/etl_config.yaml")


class MinIOConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=MINIO_ENV_PATH, env_file_encoding="utf-8"
    )
    MINIO_ROOT_USER: str  # SecretStr
    MINIO_ROOT_PASSWORD: str  # SecretStr
    MINIO_ENDPOINT: str
    BUCKET_BRONZE: str = "bronze"
    BUCKET_SILVER: str = "silver"
    BUCKET_GOLD: str = "gold"


minio_config = MinIOConfig()


class APIModel(BaseModel):
    base_url: AnyHttpUrl
    timeout: PositiveInt
    retry: PositiveInt


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
