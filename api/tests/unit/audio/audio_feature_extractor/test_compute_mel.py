from typing import TYPE_CHECKING

import numpy as np
from backend.type_aliases import FloatArray
from tests.unit.audio.audio_feature_extractor import (
    AUDIO_FEATURE_EXTRACTOR_DATA_FOLDER_PATH,
)

if TYPE_CHECKING:
    from backend.audio.audio_feature_extractor import AudioFeatureExtractor

IS_UPDATE_REFERENCE_FILE = False


def test_compute_mel(
    audio_feature_extractor: "AudioFeatureExtractor",
    audio: FloatArray,
    sample_rate: int,
) -> None:
    """Check that the compute_mel method works.

    Args:
        audio_feature_extractor (AudioFeatureExtractor): An AudioFeatureExtractor object.
        audio (FloatArray): An array corresponding to an audio.
        sample_rate (int): A sample rate.
    """
    # Check that the file containing the reference array exists
    reference_array_file_path = (
        AUDIO_FEATURE_EXTRACTOR_DATA_FOLDER_PATH
        / "test_compute_mel"
        / "reference_array.npy"
    )
    assert reference_array_file_path.exists(), (
        f"The file containing the reference array should exist "
        f"({reference_array_file_path})."
    )

    # Call the method
    array = audio_feature_extractor.compute_mel(
        audio_data=audio, sample_rate=sample_rate
    )

    # Update the reference or compare it to the returned array
    if IS_UPDATE_REFERENCE_FILE:
        np.save(reference_array_file_path, array)
    else:
        reference_array = np.load(reference_array_file_path)
        np.testing.assert_allclose(array, reference_array)
