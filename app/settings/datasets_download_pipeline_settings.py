from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .abstract_pipeline_settings import AbstractPipelineSettings, PipelineType


@dataclass
class DatasetsDownloadPipelineSettings(AbstractPipelineSettings):
    pipeline_name: str = "datasets_download_pipeline"
    pipeline_type: PipelineType = PipelineType.DOWNLOADER
    pipeline_version: str = "1.0.0"

    download_guitar_set: bool = False
    download_idmt_smt_guitar: bool = True
    base_directory = Path("./app/data/raw")

    def _to_metadata_dict(self) -> dict[str, Any]:
        return {
            "download_guitar_set": self.download_guitar_set,
            "download_idmt_smt_guitar": self.download_idmt_smt_guitar,
            "base_directory": self.base_directory.as_posix(),
        }


DATASETS_DOWNLOAD_PIPELINE_SETTINGS = DatasetsDownloadPipelineSettings()
