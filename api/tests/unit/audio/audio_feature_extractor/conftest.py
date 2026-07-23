# from typing import Any

# import numpy as np
# import pytest
# from backend.audio.audio_feature_extractor import AudioFeatureExtractor
# from numpy.typing import NDArray
# from tests.unit.audio.audio_feature_extractor import (
#     AUDIO_FEATURE_EXTRACTOR_DATA_FOLDER_PATH,
# )


# @pytest.fixture
# def audio_feature_extractor() -> AudioFeatureExtractor:
#     """Return an AudioFeatureExtractor object.

#     Returns:
#         AudioFeatureExtractor: An AudioFeatureExtractor object.
#     """
#     return AudioFeatureExtractor()


# @pytest.fixture(scope="session")
# def audio() -> NDArray[np.floating[Any]]:
#     """Return an array corresponding to an audio to give to the method.

#     Returns:
#         NDArray[np.floating[Any]]: An array corresponding to an audio.
#     """
#     audio_file_path = AUDIO_FEATURE_EXTRACTOR_DATA_FOLDER_PATH / "audio.npy"
#     assert audio_file_path.exists(), (
#         f"The path to the audio file should exist ({audio_file_path})."
#     )
#     return np.load(audio_file_path)


# @pytest.fixture(scope="session")
# def sample_rate() -> int:
#     """Return an integer corresponding to a sample_rate to give to the method.

#     Returns:
#         int: An integer corresponding to a sample_rate.
#     """
#     return 44100
