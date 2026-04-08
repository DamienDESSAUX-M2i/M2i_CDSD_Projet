from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetSettings:
    """Configuration for a dataset."""

    name: str
    urls: list[str]
    archive_names: list[str]
    extract_dir: str
    checksum: str | None = None


guitar_set_config = DatasetSettings(
    name="GuitarSet",
    urls=[
        "https://zenodo.org/api/records/3371780/files/annotation.zip/content",
        "https://zenodo.org/api/records/3371780/files/audio_hex-pickup_debleeded.zip/content",
        "https://zenodo.org/api/records/3371780/files/audio_hex-pickup_original.zip/content",
        "https://zenodo.org/api/records/3371780/files/audio_mono-mic.zip/content",
        "https://zenodo.org/api/records/3371780/files/audio_mono-pickup_mix.zip/content",
    ],
    archive_names=[
        "annotation.zip",
        "audio_hex_pickup_debleeded.zip",
        "audio_hex_pickup_original.zip",
        "audio_mono_mic.zip",
        "audio_mono_pickup_mix.zip",
    ],
    extract_dir="guitarset",
)

idmt_smt_guitar_config = DatasetSettings(
    name="IDMT-SMT-Guitar",
    urls=[
        "https://zenodo.org/api/records/7544110/files/IDMT-SMT-GUITAR_V2.zip/content"
    ],
    archive_names=["idmt_smt_guitar.zip"],
    extract_dir="idmt_smt_guitar",
)
