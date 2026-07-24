import enum
from dataclasses import asdict
from typing import TYPE_CHECKING

import numpy as np
import pytest
from api.backend.audio.audio_feature_extractor import ExtractedFeatures
from api.backend.type_aliases import FloatArray
from tests.unit.audio.audio_feature_extractor import (
    AUDIO_FEATURE_EXTRACTOR_DATA_FOLDER_PATH,
)

if TYPE_CHECKING:
    from backend.audio.audio_feature_extractor import AudioFeatureExtractor

IS_UPDATE_REFERENCE_FILE = False


class ConfigurationCase(enum.StrEnum):
    """Enumeration representing the configurations to test."""

    WITH_EXTRACTIONS = enum.auto()
    WITHOUT_EXTRACTIONS = enum.auto()


@pytest.fixture
def configuration_case(request: pytest.FixtureRequest) -> ConfigurationCase:
    """Return a ConfigurationCase value corresponding to a tested case.

    Args:
        request (pytest.FixtureRequest): A request from a parametrization.

    Returns:
        ConfigurationCase: A ConfigurationCase value.
    """
    return request.param


@pytest.fixture
def expected_extracted_features(
    configuration_case: ConfigurationCase,
) -> ExtractedFeatures:
    """Return the expected ExtractedFeatures object when calling the method.

    Args:
        configuration_case (ConfigurationCase): A ConfigurationCase value.

    Returns:
        ExtractedFeatures: The expected ExtractedFeatures object.
    """
    match configuration_case:
        case ConfigurationCase.WITH_EXTRACTIONS:
            reference_folder_path = (
                AUDIO_FEATURE_EXTRACTOR_DATA_FOLDER_PATH
                / "test_extract"
                / configuration_case
            )
            return ExtractedFeatures(
                stft_db=np.load(reference_folder_path / "stft.npy"),
                mel_db=np.load(reference_folder_path / "mel.npy"),
                cqt_db=np.load(reference_folder_path / "cqt.npy"),
                chroma=np.load(reference_folder_path / "chroma.npy"),
                mfcc=np.load(reference_folder_path / "mfcc.npy"),
            )
        case ConfigurationCase.WITHOUT_EXTRACTIONS:
            return ExtractedFeatures()


@pytest.mark.parametrize("configuration_case", ConfigurationCase, indirect=True)
def test_extract(
    configuration_case: ConfigurationCase,
    audio_feature_extractor: "AudioFeatureExtractor",
    audio: FloatArray,
    sample_rate: int,
    expected_extracted_features: ExtractedFeatures,
) -> None:
    """Check that the extract method works.

    Args:
        configuration_case (ConfigurationCase): A ConfigurationCase value.
        audio_feature_extractor (AudioFeatureExtractor): An AudioFeatureExtractor object.
        audio (FloatArray): An array corresponding to an audio.
        sample_rate (int): A sample rate.
        expected_extracted_features (ExtractedFeatures): The expected ExtractedFeatures object.
    """
    # Call the method
    extracted_features = audio_feature_extractor.extract(
        audio_data=audio,
        sample_rate=sample_rate,
        use_stft=configuration_case == ConfigurationCase.WITH_EXTRACTIONS,
        use_chroma=configuration_case == ConfigurationCase.WITH_EXTRACTIONS,
        use_cqt=configuration_case == ConfigurationCase.WITH_EXTRACTIONS,
        use_mel=configuration_case == ConfigurationCase.WITH_EXTRACTIONS,
        use_mfcc=configuration_case == ConfigurationCase.WITH_EXTRACTIONS,
    )

    # Update the reference or compare it to the returned array
    if IS_UPDATE_REFERENCE_FILE:
        if configuration_case == ConfigurationCase.WITH_EXTRACTIONS:
            reference_folder_path = (
                AUDIO_FEATURE_EXTRACTOR_DATA_FOLDER_PATH
                / "test_extract"
                / configuration_case
            )
            np.save(reference_folder_path / "stft.npy", extracted_features.stft_db)
            np.save(reference_folder_path / "mel.npy", extracted_features.mel_db)
            np.save(reference_folder_path / "cqt.npy", extracted_features.cqt_db)
            np.save(reference_folder_path / "chroma.npy", extracted_features.chroma)
            np.save(reference_folder_path / "mfcc.npy", extracted_features.mfcc)
    else:
        match configuration_case:
            case ConfigurationCase.WITH_EXTRACTIONS:
                np.testing.assert_allclose(
                    extracted_features.stft_db, expected_extracted_features.stft_db
                )
                np.testing.assert_allclose(
                    extracted_features.mel_db, expected_extracted_features.mel_db
                )
                np.testing.assert_allclose(
                    extracted_features.chroma, expected_extracted_features.chroma
                )
                np.testing.assert_allclose(
                    extracted_features.mfcc, expected_extracted_features.mfcc
                )
                np.testing.assert_allclose(
                    extracted_features.cqt_db, expected_extracted_features.cqt_db
                )
            case ConfigurationCase.WITHOUT_EXTRACTIONS:
                assert asdict(extracted_features) == asdict(expected_extracted_features)
