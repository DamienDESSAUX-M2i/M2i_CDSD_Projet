import enum
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from numpy.typing import NDArray
from tests import DATA_FOLDER_PATH

if TYPE_CHECKING:
    from app.audio.audio_cleaner import AudioCleaner


class ConfigurationCase(enum.StrEnum):
    """Configuration."""

    DEFAULT = enum.auto()
    NOT_DEFAULT = enum.auto()


@pytest.fixture()
def configuration_case(request: pytest.FixtureRequest) -> ConfigurationCase:
    """Return a ConfigurationCase value corresponding to a tested case.

    Args:
        request (pytest.FixtureRequest): _description_

    Returns:
        ConfigurationCase: _description_
    """
    return request


@pytest.fixture(scope="module")
def audio() -> NDArray[np.floating[Any]]:
    """_summary_

    Returns:
        NDArray[np.floating[Any]]: _description_
    """
    return np.load(
        DATA_FOLDER_PATH
        / "audio"
        / "audio_cleaner"
        / "test_highpass_filter"
        / "audio.npy"
    )


@pytest.fixture
def reference_array(configuration_case: ConfigurationCase) -> NDArray[np.floating[Any]]:
    """Return the reference array.

    Returns:
        NDArray[np.floating[Any]]: The reference array.
    """
    return np.load(
        DATA_FOLDER_PATH
        / "audio"
        / "audio_cleaner"
        / "test_highpass_filter"
        / f"{configuration_case}.npy"
    )


def test_default(audio_cleaner: "AudioCleaner") -> None:
    """Check that the highpass_filter method works.

    Args:
        audio_cleaner (AudioCleaner): An AudioCleaner object.
    """


@pytest.mark.parametrize("configuration_case", ConfigurationCase, indirect=True)
def test_not_default(
    configuration_case: ConfigurationCase,
    audio_cleaner: "AudioCleaner",
    audio: NDArray[np.floating[Any]],
) -> None:
    """Check that the highpass_filter method works.

    Args:
        audio_cleaner (AudioCleaner): An AudioCleaner object.
    """
    match configuration_case:
        case ConfigurationCase.DEFAULT:
            array = audio_cleaner.highpass_filter(audio=audio, sample_rate=22050)
        case ConfigurationCase.NOT_DEFAULT:
            array = audio_cleaner.highpass_filter(
                audio=audio, sample_rate=22050, cutoff=20, filter_order=1
            )
