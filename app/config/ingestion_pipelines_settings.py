import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GuitarSetIngestionPipelineConfig:
    dataset_name: str = "GuitarSet"
    dataset_path: Path = Path(
        os.getenv(
            "GUITARSET_PATH",
            "./app/data/raw/guitarset",
        )
    )
    annotation_path: Path = dataset_path / "annotation"
    audio_hex_pickup_debleeded_path: Path = dataset_path / "audio_hex-pickup_debleeded"
    audio_hex_pickup_original_path: Path = dataset_path / "audio_hex-pickup_original"
    audio_mono_mic_path: Path = dataset_path / "audio_mono-mic"
    audio_mono_pickup_mix_path: Path = dataset_path / "audio_mono-pickup_mix"
    ingestion_limit: int | None = None


guitar_set_ingestion_pipeline_config = GuitarSetIngestionPipelineConfig()


@dataclass(frozen=True)
class IDMTSMTGuitarIngestionPipelineConfig:
    dataset_name: str = "IDMT_SMT_Guitar"
    dataset_path: Path = Path(
        os.getenv(
            "IDMT_SMT_GUITAR_PATH",
            "./app/data/raw/idmt_smt_guitar/IDMT-SMT-GUITAR_V2",
        )
    )
    dataset1_path = dataset_path / "dataset1"
    dataset2_path = dataset_path / "dataset2"
    dataset3_path = dataset_path / "dataset3"
    dataset4_path = dataset_path / "dataset4"
    ingestion_limit: int | None = None


idmt_smt_guitar_ingestion_pipeline_config = IDMTSMTGuitarIngestionPipelineConfig()
