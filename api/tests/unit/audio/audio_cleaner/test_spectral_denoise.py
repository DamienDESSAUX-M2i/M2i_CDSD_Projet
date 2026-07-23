from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import NDArray
from tests.unit.audio.audio_cleaner import AUDIO_CLEANER_DATA_FOLDER_PATH

if TYPE_CHECKING:
    from backend.audio.audio_cleaner import AudioCleaner

IS_UPDATE_REFERENCE_FILE = False


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
        AUDIO_CLEANER_DATA_FOLDER_PATH / "test_spectral_denoise" / "reference_array.npy"
    )
    assert reference_array_file_path.exists(), (
        f"The file containing the reference array should exist "
        f"({reference_array_file_path})."
    )
    # Call the method
    array = audio_cleaner.spectral_denoise(audio=audio)

    # Update the reference or compare it to the returned array
    if IS_UPDATE_REFERENCE_FILE:
        np.save(reference_array_file_path, array)
    else:
        reference_array = np.load(reference_array_file_path)
        np.testing.assert_allclose(array, reference_array)
