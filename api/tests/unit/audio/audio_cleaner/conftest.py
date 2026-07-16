import pytest
from app.audio.audio_cleaner import AudioCleaner


@pytest.fixture
def audio_cleaner() -> AudioCleaner:
    """Return an AudioCleaner object.

    Returns:
        AudioCleaner: An AudioCleaner object.
    """
    return AudioCleaner()
