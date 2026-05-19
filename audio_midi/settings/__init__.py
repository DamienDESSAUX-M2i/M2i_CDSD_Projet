from pathlib import Path

from .dataset_builder_pipeline_settings import dataset_builder_pipeline_config
from .dataset_downloader_settings import DATASETS_DOWNLOADER_SETTINGS
from .datasets_download_pipeline_settings import DATASETS_DOWNLOAD_PIPELINE_SETTINGS
from .datasets_settings import GUITAR_SET_CONFIG, IDMT_SMT_GUITAR_CONFIG
from .ingestion_pipelines_settings import (
    guitar_set_ingestion_pipeline_config,
    idmt_smt_guitar_ingestion_pipeline_config,
)
from .minio_settings import minio_config
from .ml_pipeline_settings import ml_pipeline_config
from .mongodb_settings import mongo_config
from .postgresql_settings import postgres_config
from .preprocessing_pipeline_settings import preprocessing_pipeline_config

DATA_DIRECTORY = Path("./audio_midi/data").resolve()

__all__ = [
    "DATA_DIRECTORY",
    "dataset_builder_pipeline_config",
    "DATASETS_DOWNLOADER_SETTINGS",
    "GUITAR_SET_CONFIG",
    "IDMT_SMT_GUITAR_CONFIG",
    "DATASETS_DOWNLOAD_PIPELINE_SETTINGS",
    "guitar_set_ingestion_pipeline_config",
    "idmt_smt_guitar_ingestion_pipeline_config",
    "ml_pipeline_config",
    "minio_config",
    "mongo_config",
    "postgres_config",
    "preprocessing_pipeline_config",
]
