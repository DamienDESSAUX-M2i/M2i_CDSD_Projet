import enum
from typing import TYPE_CHECKING

import numpy as np
import pytest
from api.backend.audio.audio_feature_extractor import (
    FEATURE_EXTRACTOR_AUDIO_DATA_ERROR_MESSAGE,
    FEATURE_EXTRACTOR_SAMPLE_RATE_ERROR_MESSAGE,
)
from api.backend.type_aliases import FloatArray

if TYPE_CHECKING:
    from backend.audio.audio_feature_extractor import AudioFeatureExtractor


class ErrorCase(enum.StrEnum):
    """Enumeration representing the errors to test."""

    AUDIO_DATA = enum.auto()
    SAMPLE_RATE = enum.auto()


@pytest.fixture
def error_case(request: pytest.FixtureRequest) -> ErrorCase:
    """Return an ErrorCase value corresponding to a tested case.

    Args:
        request (pytest.FixtureRequest): A request from a parametrization.

    Returns:
        ErrorCase: An ErrorCase value.
    """
    return request.param


@pytest.fixture
def audio_data(error_case: ErrorCase) -> FloatArray:
    """Return the audio data to give to the method.

    Args:
        error_case (ErrorCase): An ErrorCase value.

    Returns:
        FloatArray: The audio data.
    """
    match error_case:
        case ErrorCase.AUDIO_DATA:
            return np.zeros((1, 1))
        case ErrorCase.SAMPLE_RATE:
            return np.zeros(1)


@pytest.fixture
def sample_rate(error_case: ErrorCase) -> int:
    """Return the the sample rate to give to the method.

    Args:
        error_case (ErrorCase): An ErrorCase value.

    Returns:
        int: The sample rate.
    """
    match error_case:
        case ErrorCase.AUDIO_DATA:
            return 44100
        case ErrorCase.SAMPLE_RATE:
            return -1


@pytest.fixture
def expected_message(error_case: ErrorCase) -> str:
    """Return the expected message when calling the method.

    Args:
        error_case (ErrorCase): An ErrorCase value.

    Returns:
        str: The expected message.
    """
    match error_case:
        case ErrorCase.AUDIO_DATA:
            return FEATURE_EXTRACTOR_AUDIO_DATA_ERROR_MESSAGE
        case ErrorCase.SAMPLE_RATE:
            return FEATURE_EXTRACTOR_SAMPLE_RATE_ERROR_MESSAGE


@pytest.mark.parametrize("error_case", ErrorCase, indirect=True)
def test_validate_input(
    audio_feature_extractor: "AudioFeatureExtractor",
    audio_data: FloatArray,
    sample_rate: int,
    expected_message: str,
) -> None:
    """Check that the _validate_input method works.

    Args:
        audio_feature_extractor (AudioFeatureExtractor): An AudioFeatureExtractor object.
        audio (FloatArray): An array corresponding to an audio.
        sample_rate (int): A sample rate.
        expected_message (str): The expected message.
    """
    with pytest.raises(ValueError, match=expected_message):
        audio_feature_extractor._validate_input(
            audio_data=audio_data, sample_rate=sample_rate
        )
