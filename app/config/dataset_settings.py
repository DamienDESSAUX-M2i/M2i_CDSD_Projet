from dataclasses import dataclass

from config.dataset_enum import Dataset


@dataclass(frozen=True)
class DatasetConfig:
    """Configuration for a dataset."""

    url: str
    archive_name: str
    extract_dir: str


datasets_config = {
    Dataset.GUITARSET: DatasetConfig(
        url=[
            "https://zenodo.org/api/records/3371780/files/annotation.zip/content",
            "https://zenodo.org/api/records/3371780/files/audio_hex-pickup_debleeded.zip/content",
            "https://zenodo.org/api/records/3371780/files/audio_hex-pickup_original.zip/content",
            "https://zenodo.org/api/records/3371780/files/audio_mono-mic.zip/content",
            "https://zenodo.org/api/records/3371780/files/audio_mono-pickup_mix.zip/content",
        ],
        archive_name="guitarset.zip",
        extract_dir="guitarset",
    ),
    Dataset.IDMT_SMT_GUITAR: DatasetConfig(
        url=[
            "https://zenodo.org/api/records/7544110/files/IDMT-SMT-GUITAR_V2.zip/content"
        ],
        archive_name="idmt_smt_guitar.zip",
        extract_dir="idmt_smt_guitar",
    ),
}
