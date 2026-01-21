from dataclasses import dataclass
from pathlib import Path


@dataclass
class GuitarSetIngestionPipelineConfig:
    dataset_name: str = "GuitarSet"
    dataset_path: Path = Path(
        "C:/Users/Administrateur/Documents/projet_cdsd_data/guitarset"
    )
    annotation_path: Path = Path(
        "C:/Users/Administrateur/Documents/projet_cdsd_data/guitarset/annotation"
    )
    audio_mono_pickup_mix_path: Path = Path(
        "C:/Users/Administrateur/Documents/projet_cdsd_data/guitarset/audio_mono-pickup_mix"
    )
    ingestion_limit: int = 3


guitar_set_ingestion_pipeline_config = GuitarSetIngestionPipelineConfig()
