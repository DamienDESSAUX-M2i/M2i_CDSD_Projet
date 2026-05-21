from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .abstract_pipeline_settings import AbstractPipelineSettings, PipelineType


@dataclass(frozen=True, slots=True)
class GuitarSetIngestionPipelineSettings(AbstractPipelineSettings):
    pipeline_name: str = "GuitarSet_ingestion_pipeline"
    pipeline_type: PipelineType = PipelineType.INGESTOR
    pipeline_version: str = "1.0.0"

    dataset_name: str = "GuitarSet"
    dataset_path: Path = Path("./audio_midi/data/guitarset")
    annotation_path: Path = dataset_path / "annotation"
    audio_hex_pickup_debleeded_path: Path = dataset_path / "audio_hex-pickup_debleeded"
    audio_hex_pickup_original_path: Path = dataset_path / "audio_hex-pickup_original"
    audio_mono_mic_path: Path = dataset_path / "audio_mono-mic"
    audio_mono_pickup_mix_path: Path = dataset_path / "audio_mono-pickup_mix"
    ingestion_limit: int | None = None

    def _to_metadata_dict(self) -> dict[str, Any]:
        return {}


GUITAR_SET_INGESTION_PIPELINE_SETTINGS = GuitarSetIngestionPipelineSettings()


@dataclass(frozen=True, slots=True)
class IDMTSMTGuitarIngestionPipelineSettings(AbstractPipelineSettings):
    pipeline_name: str = "IDMT_SMT_Guitar_ingestion_pipeline"
    pipeline_type: PipelineType = PipelineType.INGESTOR
    pipeline_version: str = "1.0.0"

    dataset_name: str = "IDMT_SMT_Guitar"
    dataset_path: Path = Path(
        "./audio_midi/data/idmt_smt_guitar/idmt_smt_guitar/IDMT-SMT-GUITAR_V2"
    )
    dataset1_path = dataset_path / "dataset1"
    dataset2_path = dataset_path / "dataset2"
    dataset3_path = dataset_path / "dataset3"
    dataset4_path = dataset_path / "dataset4"
    ingestion_limit: int | None = None

    def _to_metadata_dict(self) -> dict[str, Any]:
        return {}


IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS = IDMTSMTGuitarIngestionPipelineSettings()
