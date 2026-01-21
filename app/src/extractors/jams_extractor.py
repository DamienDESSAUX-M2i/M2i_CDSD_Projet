import enum
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict

import jams
import pandas as pd

from src.extractors import AbstractExtractor

SCALE_MAP = {"Gb": "F#", "Db": "C#", "Cb": "B"}


class Style(enum.StrEnum):
    """Enumeration representing the possible styles."""

    BOSSA_NOVA1 = "BN1"
    BOSSA_NOVA2 = "BN2"
    BOSSA_NOVA3 = "BN3"
    FUNK1 = "Funk1"
    FUNK2 = "Funk2"
    FUNK3 = "Funk3"
    JAZZ1 = "Jazz1"
    JAZZ2 = "Jazz2"
    JAZZ3 = "Jazz3"
    ROCK1 = "Rock1"
    ROCK2 = "Rock2"
    ROCK3 = "Rock3"
    SINGER_SONGWRITER1 = "SS1"
    SINGER_SONGWRITER2 = "SS2"
    SINGER_SONGWRITER3 = "SS3"


class Scale(enum.StrEnum):
    """Enumeration representing the possible scales."""

    A = "A"
    A_FLAT = "Ab"
    B = "B"  # Cb
    B_FLAT = "Bb"
    C = "C"
    C_SHARP = "C#"  # Db
    D = "D"
    E = "E"
    E_FLAT = "Eb"
    F = "F"
    F_SHARP = "F#"  # Gb
    G = "G"


class Version(enum.StrEnum):
    """Enumeration representing the possible versions."""

    COMPING = "comp"
    SOLO = "solo"


class Mode(enum.StrEnum):
    """Enumeration representing the scale mode."""

    MAJOR = "major"
    MINOR = "minor"


@dataclass
class JAMSMetadata:
    dataset_name: str
    guitarist_id: str
    title: str
    style: Style
    tempo: int
    scale: Scale
    mode: Mode
    version: Version
    duration: float

    def to_dict(self) -> dict:
        return {
            "dataset_name": self.dataset_name,
            "guitarist_id": self.guitarist_id,
            "title": self.title,
            "style": self.style.value,
            "tempo": self.tempo,
            "scale": self.scale.value,
            "mode": self.mode,
            "version": self.version.value,
            "duration": self.duration,
        }


class NoteMidi(TypedDict):
    data_source: str
    time: float
    duration: float
    value: float


class PitchContour(TypedDict):
    data_source: str
    time: float
    frequency: float


class BeatPosition(TypedDict):
    time: float
    position: int
    beat_units: int
    measure: int
    num_beats: int


class Chord(TypedDict):
    time: float
    duration: float
    value: str


@dataclass
class JAMSAnnotation:
    pitch_contour: pd.DataFrame
    note_midi: pd.DataFrame
    beat_position: pd.DataFrame
    chord: pd.DataFrame


class JAMSExtractor(AbstractExtractor):
    """
    JAMS file extractor.
    Extract data from a JAMS file using jams backend.
    """

    def load(self, file_path: Path, **kwargs: Any) -> jams.JAMS:
        """Load data from a JAMS file.


        Args:
            file_path (Path): Path of the JAMS file. Must end with '.jams'.
            **kwargs: Additional keyword arguments forwarded to 'jams.load'.

        Raises:
            FileNotFoundError: If the JAMS file does not exist.
            ValueError: If inputs are invalid.
            RuntimeError: If reading the JAMS file fails.

        Returns:
            jams.JAMS: jams.JAMS loaded from the JAMS file.
        """
        self._validate_file_path(file_path=file_path, suffix=".jams")

        try:
            self.logger.info(
                "Reading JAMS file",
                extra={
                    "path": str(file_path),
                },
            )
            jam = jams.load(path_or_file=str(file_path), **kwargs)
            self.logger.info(
                "JAMS extraction completed",
                extra={
                    "path": str(file_path),
                    "metadata": jam.file_metadata,
                },
            )
            return jam
        except Exception as exc:
            self.logger.exception(
                "Failed to load JAMS file.",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("JAMS extraction failed") from exc

    def extract_metadata(
        self, jam: jams.JAMS, dataset_name: str = "GuitarSet"
    ) -> JAMSMetadata:
        """Extract metadata from a jams.JAMS.

        Args:
            jam (jams.JAMS): A jams.JAMS.

        Raises:
            RunTimeError: If JAMS metadata extraction fails.

        Returns:
            JAMSMetadata: Metadata extracted from a jams.JAMS.
        """
        try:
            self.logger.info("Extracting JAMS metadata...")
            title = jam.file_metadata.title
            # Parse the title
            guitarist_id, style_tempo_scale, version = title.split("_")
            style, tempo, scale = style_tempo_scale.split("-")
            tempo = int(tempo)
            style = Style(style)
            scale = Scale(SCALE_MAP[scale] if scale not in Scale else scale)
            for jam_annotation in jam.annotations:
                if jam_annotation["namespace"] == "key_mode":
                    mode = Mode(jam_annotation["data"][0].value.split(":")[1])
                    break
            version = Version(version)
            duration = jam.file_metadata.duration
            jams_metadata = JAMSMetadata(
                dataset_name=dataset_name,
                guitarist_id=guitarist_id,
                title=title,
                style=style,
                tempo=tempo,
                scale=scale,
                mode=mode,
                version=version,
                duration=duration,
            )
            self.logger.info("JAMS metadata extracted", extra={"title": title})
            return jams_metadata
        except Exception as exception:
            self.logger.error("JAMS metadata extraction has failed")
            raise RuntimeError("JAMS metadata extraction has failed.") from exception

    def extract_annotation(self, jam: jams.JAMS) -> JAMSAnnotation:
        """Extract annotation from a jams.JAMS.

        Args:
            jam (jams.JAMS): A jams.JAMS.

        Raises:
            RunTimeError: If JAMS annotation extraction fails.

        Returns:
            JAMSAnnotation: Annotations extracted from a jams.JAMS.
        """
        try:
            self.logger.info("Extracting JAMS annotation...")
            pitch_contour: list[PitchContour] = []
            note_midi: list[NoteMidi] = []
            beat_position: list[BeatPosition] = []
            chord: list[Chord] = []
            for jam_annotation in jam.annotations:
                data_source = jam_annotation["annotation_metadata"]["data_source"]
                namespace = jam_annotation["namespace"]
                if namespace == "pitch_contour":
                    for data in jam_annotation["data"]:
                        pitch_contour.append(
                            {
                                "data_source": data_source,
                                "time": data.time,
                                "frequency": data.value["frequency"],
                            }
                        )
                if namespace == "note_midi":
                    for data in jam_annotation["data"]:
                        note_midi.append(
                            {
                                "data_source": data_source,
                                "time": data.time,
                                "duration": data.duration,
                                "value": data.value,
                            }
                        )
                if namespace == "beat_position":
                    for data in jam_annotation["data"]:
                        beat_position.append(
                            {
                                "time": data.time,
                                "position": data.value["position"],
                                "beat_units": data.value["beat_units"],
                                "measure": data.value["measure"],
                                "num_beats": data.value["num_beats"],
                            }
                        )
                if (namespace == "chord") and (data_source == ""):
                    for data in jam_annotation["data"]:
                        chord.append(
                            {
                                "time": data.time,
                                "duration": data.duration,
                                "value": data.value,
                            }
                        )
            self.logger.info(
                "JAMS annotation extracted",
                extra={
                    "pitch_contour": len(pitch_contour),
                    "note_midi": len(note_midi),
                    "beat_position": len(beat_position),
                    "chord": len(chord),
                },
            )
            return JAMSAnnotation(
                pitch_contour=pd.DataFrame(pitch_contour),
                note_midi=pd.DataFrame(note_midi),
                beat_position=pd.DataFrame(beat_position),
                chord=pd.DataFrame(chord),
            )
        except Exception as exception:
            self.logger.error(f"JAMS annotation extraction has failed: {exception}")
            raise RuntimeError("JAMS annotation extraction has failed.") from exception
