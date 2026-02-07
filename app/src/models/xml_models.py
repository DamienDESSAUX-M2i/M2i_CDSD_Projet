from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

import pandas as pd


class MicroType(StrEnum):
    SINGLE_COIL = "SC"
    HUMBUCKER = "HU"


class GuitarType(StrEnum):
    ELECTRIC_GUITAR = "EGUI"


class GuitarBrand(StrEnum):
    FENDER = "Fender"
    IBANEZ = "Ibanez"


class GuitarModel(StrEnum):
    STRATOCASTER = "Strat"
    POWER_STRATOCASTER = "Power Strat"


class AmpChannel(StrEnum):
    CLEAN = "Clean"


class MicroPosition(StrEnum):
    NECK = "Neck"
    BRIDGE = "Bridge"
    NECK_BRIDGE = "Bridge+Neck"


@dataclass
class XMLMetadata:
    dataset_name: str
    title: str
    instrument: str
    instrument_model: str
    pick_up_setting: str
    # pick_up_type: str
    instrument_tuning: str
    # amp_channel: str
    audio_effects: str
    recording_date: str
    recording_artist: str
    instrument_body_material: str
    instrument_string_material: str
    composer: str
    recording_source: str
    # polyphony: bool

    def to_dict(self) -> dict:
        return {
            "dataset_name": self.dataset_name,
            "audio_file_name": self.title,
            "instrument": self.instrument,
            "instrument_model": self.instrument_model,
            "pick_up_setting": self.pick_up_setting,
            # "pick_up_type": self.pick_up_type,
            "instrument_tuning": self.instrument_tuning,
            # "amp_channel": self.amp_channel,
            "audio_effects": self.audio_effects,
            "recording_date": self.recording_date,
            "recording_artist": self.recording_artist,
            "instrument_body_material": self.instrument_body_material,
            "instrument_string_material": self.instrument_string_material,
            "composer": self.composer,
            "recording_source": self.recording_source,
            # "polyphony": self.polyphony,
        }


class ExcitationStyle(StrEnum):
    FINGER_STYLE = "FS"
    MUTED = "MU"
    PICKED = "PK"


class ExpressionStyle(StrEnum):
    BENDING = "DE"
    DEAD_NOTES = "DN"
    FLUTTER = "FL"
    HARMONICS = "HA"
    NO_EXPRESSION_SYTLE = "NO"
    SLIDE = "SL"
    STACCATO = "ST"
    TREMOLO = "TR"
    VIBRATO = "VI"


class Loudness(StrEnum):
    PIANISSISSIMO = "ppp"
    PIANISSIMO = "pp"
    PIANO = "p"
    MEZZO_PIANO = "mp"
    MEZZO_FORTE = "mf"
    FORTE = "f"
    FORTISSIMO = "ff"
    FORTISSISSIMO = "fff"


@dataclass
class Event:
    pitch: int | None
    onset: float | None
    offset: float | None
    fret_number: int | None
    string_number: int | None
    excitation_style: ExcitationStyle | None
    expression_style: ExpressionStyle | None
    loudness: Loudness | None
    modulation_frequency_range: float | None
    modulation_frequency: float | None

    def to_dict(self) -> dict:
        return {
            "pitch": self.pitch,
            "onset": self.onset,
            "offset": self.offset,
            "fret_number": self.fret_number,
            "string_number": self.string_number,
            "excitation_style": self.excitation_style.name.lower()
            if self.excitation_style
            else None,
            "expression_style": self.expression_style.name.lower()
            if self.expression_style
            else None,
            "loudness": self.loudness.name.lower() if self.loudness else None,
            "modulation_frequency_range": self.modulation_frequency_range,
            "modulation_frequency": self.modulation_frequency,
        }


@dataclass
class XMLAnnotation:
    dataset_name: str
    title: str
    transcription: pd.DataFrame

    def to_dict(
        self,
        **kwargs,
    ) -> dict[str, str]:
        """Convert DataFrame into dictionary with 'records' orientation.

        Args:
            **kwargs: Additional keyword arguments forwarded to 'pandas.DataFrame.to_dict'.

        Returns:
            dict[str, str]: Dictionary whose keys are attributes of the XMLAnnotation class
            and values are strings (DataFrame converted into dictionary).
        """
        return {
            "dataset_name": self.dataset_name,
            "title": self.title,
            "transcription": self.transcription.to_dict(orient="records", **kwargs),
        }
