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
