from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatasetSettings:
    """
    Immutable configuration describing a dataset download specification.

    This model binds together remote dataset artifacts, their local
    representation, and extraction configuration.

    Attributes:
        name: Name of the dataset.
        urls: Tuple of remote URLs pointing to dataset archives.
        archive_names: Tuple of local archive filenames corresponding
            one-to-one with `urls`.
        extract_dir: Directory where archives are extracted.
    """

    name: str
    urls: tuple[str, ...]
    archive_names: tuple[str, ...]
    extract_dir_name: str

    def __post_init__(self) -> None:
        """
        Validate dataset configuration invariants.

        Ensures structural consistency and prevents misconfiguration
        of dataset download specifications.

        Raises:
            ValueError: If configuration is invalid or inconsistent.
        """

        if not self.name.strip():
            raise ValueError("name must be a non-empty string")

        if not self.urls:
            raise ValueError("urls must not be empty")

        if len(self.urls) != len(self.archive_names):
            raise ValueError("urls and archive_names must have the same length")

        if not self.extract_dir_name.strip():
            raise ValueError("extract_dir_name must be a non-empty string")


GUITAR_SET_SETTINGS = DatasetSettings(
    name="GuitarSet",
    urls=(
        "https://zenodo.org/api/records/3371780/files/annotation.zip/content",
        "https://zenodo.org/api/records/3371780/files/audio_hex-pickup_debleeded.zip/content",
        "https://zenodo.org/api/records/3371780/files/audio_hex-pickup_original.zip/content",
        "https://zenodo.org/api/records/3371780/files/audio_mono-mic.zip/content",
        "https://zenodo.org/api/records/3371780/files/audio_mono-pickup_mix.zip/content",
    ),
    archive_names=(
        "annotation.zip",
        "audio_hex-pickup_debleeded.zip",
        "audio_hex-pickup_original.zip",
        "audio_mono-mic.zip",
        "audio_mono-pickup_mix.zip",
    ),
    extract_dir_name="guitarset",
)

IDMT_SMT_GUITAR_SETTINGS = DatasetSettings(
    name="IDMT-SMT-Guitar",
    urls=(
        "https://zenodo.org/api/records/7544110/files/IDMT-SMT-GUITAR_V2.zip/content",
    ),
    archive_names=("idmt_smt_guitar.zip",),
    extract_dir_name="idmt_smt_guitar",
)
