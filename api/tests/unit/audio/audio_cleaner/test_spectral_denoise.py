from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from numpy.typing import NDArray
from tests import DATA_FOLDER_PATH

if TYPE_CHECKING:
    from app.audio.audio_cleaner import AudioCleaner

IS_UPDATE_REFERENCE_FILE = True


@pytest.fixture
def audio() -> NDArray[np.floating[Any]]:
    """Return an array corresponding to an audio to give to the method.

    Returns:
        NDArray[np.floating[Any]]: An array corresponding to an audio.
    """
    audio_file_path = (
        DATA_FOLDER_PATH
        / "unit"
        / "audio"
        / "audio_cleaner"
        / "test_spectral_denoise"
        / "audio.npy"
    )
    assert audio_file_path.exists(), (
        f"The path to the audio file should exist ({audio_file_path})."
    )
    return np.load(audio_file_path)


def test_spectral_denoise(
    audio_cleaner: "AudioCleaner",
    audio: NDArray[np.floating[Any]],
) -> None:
    """Check that the spectral_denoise method works.

    Args:
        audio_cleaner (AudioCleaner): An AudioCleaner object.
        audio (NDArray[np.floating[Any]]): An array corresponding to an audio.
    """
    # Check that the file containing the reference array exists
    reference_array_file_path = (
        DATA_FOLDER_PATH
        / "unit"
        / "audio"
        / "audio_cleaner"
        / "test_spectral_denoise"
        / "reference_array.npy"
    )
    assert reference_array_file_path.exists(), (
        f"The file containing the reference array should exist ({reference_array_file_path})."
    )
    # Call the method
    array = audio_cleaner.spectral_denoise(audio=audio)

    # Update the reference or compare it to the returned array
    if IS_UPDATE_REFERENCE_FILE:
        np.save(reference_array_file_path, array)
    else:
        reference_array = np.load(reference_array_file_path)
        np.testing.assert_allclose(array, reference_array)
