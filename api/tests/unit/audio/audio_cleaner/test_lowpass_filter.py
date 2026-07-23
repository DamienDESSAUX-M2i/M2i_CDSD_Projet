import enum
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from numpy.typing import NDArray
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
def test_lowpass_filter(
    configuration_case: ConfigurationCase,
    audio_cleaner: "AudioCleaner",
    audio: NDArray[np.floating[Any]],
    sample_rate: int,
) -> None:
    """Check that the lowpass_filter method works.

    Args:
        configuration_case (ConfigurationCase): A ConfigurationCase value.
        audio_cleaner (AudioCleaner): An AudioCleaner object.
        audio (NDArray[np.floating[Any]]): An array corresponding to an audio.
        sample_rate (int): An integer corresponding to a sample_rate.
    """
    # Check that the file containing the reference array exists
    reference_array_file_path = (
        AUDIO_CLEANER_DATA_FOLDER_PATH
        / "test_lowpass_filter"
        / f"{configuration_case}_reference_array.npy"
    )
    assert reference_array_file_path.exists(), (
        f"The file containing the reference array should exist "
        f"({reference_array_file_path})."
    )

    # Call the method
    match configuration_case:
        case ConfigurationCase.DEFAULT:
            array = audio_cleaner.lowpass_filter(audio=audio, sample_rate=sample_rate)
        case ConfigurationCase.NOT_DEFAULT:
            array = audio_cleaner.lowpass_filter(
                audio=audio, sample_rate=sample_rate, cutoff=20, filter_order=1
            )

    # Update the reference or compare it to the returned array
    if IS_UPDATE_REFERENCE_FILE:
        np.save(reference_array_file_path, array)
    else:
        reference_array = np.load(reference_array_file_path)
        np.testing.assert_allclose(array, reference_array)
