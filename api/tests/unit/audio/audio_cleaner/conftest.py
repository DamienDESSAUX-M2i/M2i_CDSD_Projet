import numpy as np
import pytest
from api.backend.type_aliases import FloatArray
from backend.audio.audio_cleaner import AudioCleaner
from tests.unit.audio.audio_cleaner import AUDIO_CLEANER_DATA_FOLDER_PATH


@pytest.fixture
def audio_cleaner() -> AudioCleaner:
    """Return an AudioCleaner object.

    Returns:
        AudioCleaner: An AudioCleaner object.
    """
    return AudioCleaner()


@pytest.fixture(scope="session")
def audio() -> FloatArray:
    """Return an array corresponding to an audio to give to the method.

    Returns:
        FloatArray: An array corresponding to an audio.
    """
    audio_file_path = AUDIO_CLEANER_DATA_FOLDER_PATH / "audio.npy"
    assert audio_file_path.exists(), (
        f"The path to the audio file should exist ({audio_file_path})."
    )
    return np.load(audio_file_path)


@pytest.fixture(scope="session")
def sample_rate() -> int:
    """Return an integer corresponding to a sample_rate to give to the method.

    Returns:
        int: An integer corresponding to a sample_rate.
    """
    return 44100
