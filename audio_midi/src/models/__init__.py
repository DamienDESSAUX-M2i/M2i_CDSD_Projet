from enum import StrEnum

from .jams_models import (
    SCALE_MAP,
    BeatPositionDict,
    ChordDict,
    JAMSAnnotation,
    JAMSMetadata,
    Mode,
    NoteMidiDict,
    PitchContourDict,
    PlayingVersion,
    Scale,
    Style,
)
from .xml_models import (
    AmpChannel,
    Event,
    EventDict,
    ExcitationStyle,
    ExpressionStyle,
    GuitarBrand,
    GuitarModel,
    GuitarType,
    Loudness,
    MicroPosition,
    MicroType,
    XMLAnnotation,
    XMLMetadata,
)


class AnnotationType(StrEnum):
    """Enumeration representing annotation type."""

    JAMS = "jams"
    XML = "xml"
    TXT = "txt"
    CSV = "csv"


class AudioType(StrEnum):
    """Enumeration representing audio type."""

    AUDIO_MONO_PICKUP_MIX = "audio_mono-pickup_mix"
    AUDIO_HEX_PICKUP_DEBLEEDED = "audio_hex-pickup_debleeded"
    AUDIO_HEX_PICKUP_ORIGINAL = "audio_hex-pickup_original"
    AUDIO_MONO_MIC = "audio_mono-mic"
    WAV = "wav"
    PROCESSED_AUDIO = "processed_audio"
    UNKNOWN = "unknown"


__all__ = [
    "AnnotationType",
    "SCALE_MAP",
    "BeatPositionDict",
    "ChordDict",
    "JAMSAnnotation",
    "JAMSMetadata",
    "Mode",
    "NoteMidiDict",
    "PitchContourDict",
    "PlayingVersion",
    "Scale",
    "Style",
    "AmpChannel",
    "Event",
    "EventDict",
    "ExcitationStyle",
    "ExpressionStyle",
    "GuitarBrand",
    "GuitarModel",
    "GuitarType",
    "Loudness",
    "MicroPosition",
    "MicroType",
    "XMLAnnotation",
    "XMLMetadata",
]
