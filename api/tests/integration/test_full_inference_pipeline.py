import numpy as np
import pytest
import soundfile as sf
from backend.core import PROCESSING_SETTINGS, ModelManager  # type: ignore
from backend.services import (  # type: ignore
    InferenceResult,
    InferenceService,
    PostprocessingResult,
    PostprocessingService,
    PreprocessingResult,
    PreprocessingService,
)
from backend.type_aliases import FloatArray
from numpy.typing import NDArray

from tests import METADATA_PATH, MODEL_PATH, SCALER_PATH
from tests.integration import INTEGRATION_DATA_FOLDER_PATH

AUDIO_PATH = INTEGRATION_DATA_FOLDER_PATH / "00_BN1-129-Eb_comp_mix.wav"


@pytest.mark.skip(reason="Can not be launched on windows.")
def test_full_inference_pipeline() -> None:
    preprocessing = PreprocessingService(settings=PROCESSING_SETTINGS)
    manager = ModelManager(
        model_path=MODEL_PATH,
        scaler_path=SCALER_PATH,
        metadata_path=METADATA_PATH,
    )
    inference = InferenceService(model_manager=manager)
    postprocessing = PostprocessingService(settings=PROCESSING_SETTINGS)

    audio_data, sample_rate = sf.read(AUDIO_PATH.as_posix())

    # soundfile returns (samples, channels)
    # librosa expects (channels, samples)
    if audio_data.ndim == 2:
        audio_data = audio_data.T

    preprocessing_result = preprocessing.preprocess(
        audio=audio_data,
        sample_rate=sample_rate,
    )
    assert isinstance(preprocessing_result, PreprocessingResult)
    assert preprocessing_result.features.shape == 12
    assert isinstance(preprocessing_result.features, FloatArray)

    inference_result = inference.infer(preprocessing_result.features)
    assert isinstance(inference_result, InferenceResult)
    assert inference_result.piano_roll.shape == 12
    assert isinstance(inference_result.piano_roll, NDArray[np.bool_])
    assert inference_result.probabilities.shape == 12
    assert isinstance(inference_result.probabilities, FloatArray)

    postprocessing_result = postprocessing.process(
        processing_id="test",
        piano_roll=inference_result.piano_roll,
        audio=preprocessing_result.audio,
        sample_rate=preprocessing_result.sample_rate,
    )
    assert isinstance(postprocessing_result, PostprocessingResult)
    assert postprocessing_result.piano_roll_png_path.exists()
    assert postprocessing_result.piano_roll_svg_path.exists()
    assert postprocessing_result.midi_path.exists()
    assert postprocessing_result.musicxml_path.exists()
    assert postprocessing_result.score_pdf_path is not None
    assert postprocessing_result.score_pdf_path.exists()
    assert postprocessing_result.score_svg_path is not None
    assert postprocessing_result.score_svg_path.exists()
