from pathlib import Path

from .dataset_builder_pipeline_settings import dataset_builder_pipeline_config
from .dataset_downloader_settings import DATASETS_DOWNLOADER_SETTINGS
from .datasets_settings import GUITAR_SET_SETTINGS, IDMT_SMT_GUITAR_SETTINGS
from .ingestion_pipelines_settings import (
    GUITAR_SET_INGESTION_PIPELINE_SETTINGS,
    IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS,
)
from .minio_settings import MINIO_SETTINGS
from .ml_pipeline_settings import ml_pipeline_config
from .mongo_settings import MONGO_SETTINGS
from .postgres_settings import POSTGRES_SETTINGS
from .preprocessing_pipeline_settings import PREPROCESSING_PIPELINE_SETTINGS

DATA_DIRECTORY = Path("./audio_midi/data").resolve()

__all__ = [
    "DATA_DIRECTORY",
    "dataset_builder_pipeline_config",
    "DATASETS_DOWNLOADER_SETTINGS",
    "GUITAR_SET_SETTINGS",
    "IDMT_SMT_GUITAR_SETTINGS",
    "GUITAR_SET_INGESTION_PIPELINE_SETTINGS",
    "IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS",
    "ml_pipeline_config",
    "MINIO_SETTINGS",
    "MONGO_SETTINGS",
    "POSTGRES_SETTINGS",
    "PREPROCESSING_PIPELINE_SETTINGS",
]
