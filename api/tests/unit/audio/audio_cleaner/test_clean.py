import enum
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from backend.audio.audio_cleaner import DenoiseMethod
from numpy.typing import NDArray
from tests import DATA_FOLDER_PATH

if TYPE_CHECKING:
    from backend.audio.audio_cleaner import AudioCleaner

IS_UPDATE_REFERENCE_FILE = True


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


@pytest.fixture(scope="module")
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
        / "test_clean"
        / "audio.npy"
    )
    assert audio_file_path.exists(), (
        f"The path to the audio file should exist ({audio_file_path})."
    )
    return np.load(audio_file_path)


@pytest.mark.parametrize("configuration_case", ConfigurationCase, indirect=True)
def test_clean(
    configuration_case: ConfigurationCase,
    audio_cleaner: "AudioCleaner",
    audio: NDArray[np.floating[Any]],
) -> None:
    """Check that the clean method works.

    Args:
        configuration_case (ConfigurationCase): A ConfigurationCase value.
        audio_cleaner (AudioCleaner): An AudioCleaner object.
        audio (NDArray[np.floating[Any]]): An array corresponding to an audio.
    """
    # Check that the file containing the reference array exists
    reference_array_file_path = (
        DATA_FOLDER_PATH
        / "unit"
        / "audio"
        / "audio_cleaner"
        / "test_clean"
        / f"{configuration_case}_reference_array.npy"
    )
    assert reference_array_file_path.exists(), (
        f"The file containing the reference array should exist ({reference_array_file_path})."
    )

    # Call the method
    match configuration_case:
        case ConfigurationCase.FILTERING_DENOISE_SPECTRAL:
            array = audio_cleaner.clean(
                audio=audio,
                use_highpass=True,
                use_lowpass=True,
                denoise_method=DenoiseMethod.SPECTRAL,
                use_trim=True,
            )
        case ConfigurationCase.FILTERING_DENOISE_WIENER:
            array = audio_cleaner.clean(
                audio=audio,
                use_highpass=True,
                use_lowpass=True,
                denoise_method=DenoiseMethod.WIENER,
                use_trim=True,
            )
        case ConfigurationCase.NO_FILTERING:
            array = audio_cleaner.clean(
                audio=audio,
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
        np.testing.assert_allclose(array, reference_array)
