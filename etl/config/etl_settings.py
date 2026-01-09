from pathlib import Path
from typing import Tuple, Type

from pydantic import AnyHttpUrl, BaseModel, PositiveInt
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

ETL_SETTINGS_PATH = Path("/app/config/etl_config.yaml")


class APIModel(BaseModel):
    base_url: AnyHttpUrl
    endpoint: str
    delay: float
    timeout: PositiveInt = 30
    max_retries: PositiveInt = 3


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
