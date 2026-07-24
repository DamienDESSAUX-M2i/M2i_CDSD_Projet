import enum
from typing import TYPE_CHECKING

import numpy as np
import pytest
from backend.audio.audio_cleaner import DenoiseMethod
from backend.type_aliases import FloatArray
from tests.unit.audio.audio_cleaner import AUDIO_CLEANER_DATA_FOLDER_PATH

if TYPE_CHECKING:
    from backend.audio.audio_cleaner import AudioCleaner

IS_UPDATE_REFERENCE_FILE = False


class ConfigurationCase(enum.StrEnum):
    """Configuration."""

    FILTERING_DENOISE_SPECTRAL = enum.auto()
    FILTERING_DENOISE_WIENER = enum.auto()
    NO_FILTERING = enum.auto()


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
def test_clean(
    configuration_case: ConfigurationCase,
    audio_cleaner: "AudioCleaner",
    audio: FloatArray,
    sample_rate: int,
) -> None:
    """Check that the clean method works.

    Args:
        configuration_case (ConfigurationCase): A ConfigurationCase value.
        audio_cleaner (AudioCleaner): An AudioCleaner object.
        audio (FloatArray): An array corresponding to an audio.
        sample_rate (int): An integer corresponding to a sample_rate.
    """
    # Check that the file containing the reference array exists
    reference_array_file_path = (
        AUDIO_CLEANER_DATA_FOLDER_PATH
        / "test_clean"
        / f"{configuration_case}_reference_array.npy"
    )
    assert reference_array_file_path.exists(), (
        f"The file containing the reference array should exist "
        f"({reference_array_file_path})."
    )

    # Call the method
    match configuration_case:
        case ConfigurationCase.FILTERING_DENOISE_SPECTRAL:
            array = audio_cleaner.clean(
                audio=audio,
                sample_rate=sample_rate,
                use_highpass=True,
                use_lowpass=True,
                denoise_method=DenoiseMethod.SPECTRAL,
                use_trim=True,
            )
        case ConfigurationCase.FILTERING_DENOISE_WIENER:
            array = audio_cleaner.clean(
                audio=audio,
                sample_rate=sample_rate,
                use_highpass=True,
                use_lowpass=True,
                denoise_method=DenoiseMethod.WIENER,
                use_trim=True,
            )
        case ConfigurationCase.NO_FILTERING:
            array = audio_cleaner.clean(
                audio=audio,
                sample_rate=sample_rate,
                use_highpass=False,
                use_lowpass=False,
                denoise_method=DenoiseMethod.NONE,
                use_trim=False,
            )

    # Update the reference or compare it to the returned array
    if IS_UPDATE_REFERENCE_FILE:
        np.save(reference_array_file_path, array)
    else:
        reference_array = np.load(reference_array_file_path)
        np.testing.assert_allclose(array, reference_array, rtol=1e-5)
