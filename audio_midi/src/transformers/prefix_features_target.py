from enum import StrEnum


class PrefixFeaturesTarget(StrEnum):
    TARGET = "midi_pitch"
    STFT = "stft"
    MEL_SPECTROGRAM = "mel"
    CQT = "cqt"
    CQT_CHROMAGRAM = "chroma"
    MFCC = "mfcc"
