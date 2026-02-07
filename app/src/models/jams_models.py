from dataclasses import dataclass
from enum import StrEnum
from typing import TypedDict

import pandas as pd

SCALE_MAP = {"Gb": "F#", "Db": "C#", "Cb": "B"}


class Style(StrEnum):
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


class Scale(StrEnum):
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


class PlayingVersion(StrEnum):
    """Enumeration representing the possible versions."""

    COMPING = "comp"
    SOLO = "solo"


class Mode(StrEnum):
    """Enumeration representing the scale mode."""

    MAJOR = "major"
    MINOR = "minor"


@dataclass
class JAMSMetadata:
    dataset_name: str
    guitarist_id: int
    title: str
    style: Style
    tempo: int
    scale: Scale
    mode: Mode
    playing_version: PlayingVersion
    duration: float
    pick_up_setting: str | None

    def to_dict(self) -> dict:
        return {
            "dataset_name": self.dataset_name,
            "guitarist_id": self.guitarist_id,
            "title": self.title,
            "style": self.style.name.lower(),
            "tempo": self.tempo,
            "scale": self.scale.name.lower(),
            "mode": self.mode,
            "version": self.playing_version.name.lower(),
            "duration": self.duration,
            "pick_up_setting": self.pick_up_setting,
        }


class PitchContourDict(TypedDict):
    dataset_name: str
    title: str
    data_source: str
    time: float
    frequency: float


class NoteMidiDict(TypedDict):
    dataset_name: str
    title: str
    data_source: str
    time: float
    duration: float
    value: float


class BeatPositionDict(TypedDict):
    dataset_name: str
    title: str
    time: float
    position: int
    beat_units: int
    measure: int
    num_beats: int


class ChordDict(TypedDict):
    dataset_name: str
    title: str
    time: float
    duration: float
    value: str


@dataclass
class JAMSAnnotation:
    dataset_name: str
    title: str
    pitch_contour: pd.DataFrame
    note_midi: pd.DataFrame
    beat_position: pd.DataFrame
    chord: pd.DataFrame

    def to_dict(
        self,
        **kwargs,
    ) -> dict[str, str]:
        """Convert DataFrames into dictionaries with 'records' orientation.

        Args:
            **kwargs: Additional keyword arguments forwarded to 'pandas.DataFrame.to_dict'.

        Returns:
            dict[str, str]: Dictionary whose keys are attributes of the JAMSAnnotation class
            and values are DataFrame converted into dictionaries.
        """
        return {
            "pitch_contour": {
                "dataset_name": self.dataset_name,
                "title": self.title,
                "pitch_contour": self.pitch_contour.to_dict(orient="records", **kwargs),
            },
            "note_midi": {
                "dataset_name": self.dataset_name,
                "title": self.title,
                "note_midi": self.note_midi.to_dict(orient="records", **kwargs),
            },
            "beat_position": {
                "dataset_name": self.dataset_name,
                "title": self.title,
                "beat_position": self.beat_position.to_dict(orient="records", **kwargs),
            },
            "chord": {
                "dataset_name": self.dataset_name,
                "title": self.title,
                "chord": self.chord.to_dict(orient="records", **kwargs),
            },
        }
