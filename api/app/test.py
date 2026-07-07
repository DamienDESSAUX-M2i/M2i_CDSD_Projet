import logging
from pathlib import Path

import soundfile as sf
from core import PROCESSING_SETTINGS
from services.preprocessing_service import PreprocessingService

AUDIO_PATH = Path(__file__).parent.resolve() / "00_BN1-129-Eb_comp_mix.wav"


def main() -> None:
    logging.basicConfig()

    preprocessing = PreprocessingService(settings=PROCESSING_SETTINGS)

    audio_data, sample_rate = sf.read(AUDIO_PATH.as_posix())

    # soundfile returns (samples, channels)
    # librosa expects (channels, samples)
    if audio_data.ndim == 2:
        audio_data = audio_data.T

    features = preprocessing.preprocess(
        audio=audio_data,
        sample_rate=sample_rate,
    )

    print(f"Output shape : {features.shape}")
    print(f"dtype        : {features.dtype}")
    print(features)


if __name__ == "__main__":
    main()
