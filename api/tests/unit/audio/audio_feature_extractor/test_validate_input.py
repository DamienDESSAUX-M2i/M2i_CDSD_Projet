# import enum
# from typing import TYPE_CHECKING

# import pytest

# if TYPE_CHECKING:
#     from backend.audio.audio_feature_extractor import AudioFeatureExtractor

# IS_UPDATE_REFERENCE_FILE = False


# class ErrorCase(enum.StrEnum):
#     """Enumeration representing the errors to test."""

#     DEFAULT = enum.auto()
#     NOT_DEFAULT = enum.auto()


# @pytest.fixture
# def error_case(request: pytest.FixtureRequest) -> ErrorCase:
#     """Return an ErrorCase value corresponding to a tested case.

#     Args:
#         request (pytest.FixtureRequest): A request from a parametrization.

#     Returns:
#         ErrorCase: An ErrorCase value.
#     """
#     return request.param


# @pytest.fixture(scope="session")
# def expected_message(error_case: ErrorCase) -> str:
#     """Return the expected message when calling the method.

#     Args:
#         error_case (ErrorCase): An ErrorCase value.

#     Returns:
#         str: The expected message.
#     """
#     return 44100


# @pytest.mark.parametrize("error_case", ErrorCase, indirect=True)
# def test_validate_input(
#     audio_feature_extractor: "AudioFeatureExtractor",
# ) -> None:
#     """Check that the _validate_input method works.

#     Args:
#         audio_feature_extractor (AudioFeatureExtractor): An AudioFeatureExtractor object.
#         audio (NDArray[np.floating[Any]]): An array corresponding to an audio.
#     """
#     with pytest.raises(ValueError, match=expected_message):
#         audio_feature_extractor._validate_input()
