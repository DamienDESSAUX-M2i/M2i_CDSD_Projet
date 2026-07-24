import enum
from typing import TYPE_CHECKING

import numpy as np
import pytest
from api.backend.type_aliases import FloatArray
from tests.unit.audio.audio_cleaner import AUDIO_CLEANER_DATA_FOLDER_PATH

if TYPE_CHECKING:
    from backend.audio.audio_cleaner import AudioCleaner

IS_UPDATE_REFERENCE_FILE = False


class ConfigurationCase(enum.StrEnum):
    """Configuration."""

    DEFAULT = enum.auto()
    NOT_DEFAULT = enum.auto()


@pytest.fixture
def configuration_case(request: pytest.FixtureRequest) -> ConfigurationCase:
    """Return a ConfigurationCase value corresponding to a tested case.

    Args:
        request (pytest.FixtureRequest): A request from a parametrization.

    Returns:
        ConfigurationCase: A ConfigurationCase value.
    """
    return request.param


@pytest.mark.parametrize("configuration_case", ConfigurationCase, indirect=True)
def test_wiener_denoise(
    configuration_case: ConfigurationCase,
    audio_cleaner: "AudioCleaner",
    audio: FloatArray,
) -> None:
    """Check that the wiener_denoise method works.

    Args:
        configuration_case (ConfigurationCase): A ConfigurationCase value.
        audio_cleaner (AudioCleaner): An AudioCleaner object.
        audio (FloatArray): An array corresponding to an audio.
    """
    # Check that the file containing the reference array exists
    reference_array_file_path = (
        AUDIO_CLEANER_DATA_FOLDER_PATH
        / "test_wiener_denoise"
        / f"{configuration_case}_reference_array.npy"
    )
    assert reference_array_file_path.exists(), (
        f"The file containing the reference array should exist "
        f"({reference_array_file_path})."
    )

    # Call the method
    match configuration_case:
        case ConfigurationCase.DEFAULT:
            array = audio_cleaner.wiener_denoise(audio=audio)
        case ConfigurationCase.NOT_DEFAULT:
            array = audio_cleaner.wiener_denoise(audio=audio, strength=2)

    # Update the reference or compare it to the returned array
    if IS_UPDATE_REFERENCE_FILE:
        np.save(reference_array_file_path, array)
    else:
        reference_array = np.load(reference_array_file_path)
        np.testing.assert_allclose(array, reference_array)
