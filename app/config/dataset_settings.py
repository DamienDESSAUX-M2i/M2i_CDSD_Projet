from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetSettings:
    """Configuration for a dataset."""

    name: str
    urls: list[str]
    archive_name: str
    extract_dir: str
    checksum: str | None = None


guitar_set_config = DatasetSettings(
    name="GuitarSet",
    urs=[
        "https://zenodo.org/api/records/3371780/files/annotation.zip/content",
        "https://zenodo.org/api/records/3371780/files/audio_hex-pickup_debleeded.zip/content",
        "https://zenodo.org/api/records/3371780/files/audio_hex-pickup_original.zip/content",
        "https://zenodo.org/api/records/3371780/files/audio_mono-mic.zip/content",
        "https://zenodo.org/api/records/3371780/files/audio_mono-pickup_mix.zip/content",
    ],
    archive_name="guitarset.zip",
    extract_dir="guitarset",
)

idmt_smt_guitar_config = DatasetSettings(
    name="IDMT-SMT-Guitar",
    urls=[
        "https://zenodo.org/api/records/7544110/files/IDMT-SMT-GUITAR_V2.zip/content"
    ],
    archive_name="idmt_smt_guitar.zip",
    extract_dir="idmt_smt_guitar",
)
