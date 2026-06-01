from enum import StrEnum

from .abstract_transformer import AbstractTransformer
from .audio_cleaner import AudioCleaner, DenoiseMethod
from .audio_features_extractor import AudioFeatureExtractor
from .audio_normalizer import AudioNormalizer, NormalizationType
from .element_tree_wrapper import ElementTreeWrapper


class PrefixFeaturesTarget(StrEnum):
    TARGET = "midi_pitch"
    STFT = "stft"
    MEL_SPECTROGRAM = "mel"
    CQT = "cqt"
    CQT_CHROMAGRAM = "chroma"
    MFCC = "mfcc"


__all__ = [
    "AbstractTransformer",
    "AudioCleaner",
    "DenoiseMethod",
    "AudioFeatureExtractor",
    "AudioNormalizer",
    "NormalizationType",
    "ElementTreeWrapper",
    "PrefixFeaturesTarget",
]
