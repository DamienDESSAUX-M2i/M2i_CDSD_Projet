import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GuitarSetIngestionPipelineConfig:
    dataset_name: str = "GuitarSet"
    dataset_path: Path = Path(
        os.getenv(
            "GUITARSET_PATH",
            "C:/Users/Administrateur/Documents/projet_cdsd_data/guitarset",
        )
    )
    annotation_path: Path = dataset_path / "annotation"
    audio_hex_pickup_debleeded_path: Path = dataset_path / "audio_hex-pickup_debleeded"
    audio_hex_pickup_original_path: Path = dataset_path / "audio_hex-pickup_original"
    audio_mono_mic_path: Path = dataset_path / "audio_mono-mic"
    audio_mono_pickup_mix_path: Path = dataset_path / "audio_mono-pickup_mix"
    ingestion_limit: int = 3


guitar_set_ingestion_pipeline_config = GuitarSetIngestionPipelineConfig()
