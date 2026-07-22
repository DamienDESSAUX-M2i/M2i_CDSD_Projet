import logging
from pathlib import Path

import soundfile as sf

from core import PROCESSING_SETTINGS, ModelManager  # type: ignore
from services import (  # type: ignore
    InferenceService,
    PostprocessingService,
    PreprocessingService,
)

API_DIR = Path(__file__).parent.resolve()
AUDIO_PATH = API_DIR / "00_BN1-129-Eb_comp_mix.wav"
MODEL_PATH = API_DIR / "artifacts" / "model.keras"
SCALER_PATH = None
METADATA_PATH = API_DIR / "artifacts" / "metadata.json"


def main() -> None:
    logging.basicConfig()

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

    print(f"Preprocessing time: {preprocessing_result.preprocessing_time}")
    print(f"Output shape      : {preprocessing_result.features.shape}")
    print(f"dtype             : {preprocessing_result.features.dtype}")

    inference_result = inference.infer(preprocessing_result.features)

    print(f"Inference time     : {inference_result.inference_time}")
    print(f"Piano roll shape   : {inference_result.piano_roll.shape}")
    print(f"Piano roll dtype   : {inference_result.piano_roll.dtype}")
    print(f"Probabilities shape: {inference_result.probabilities.shape}")
    print(f"Probabilities dtype: {inference_result.probabilities.dtype}")

    postprocessing_result = postprocessing.process(
        processing_id="test",
        piano_roll=inference_result.piano_roll,
        audio=preprocessing_result.audio,
        sample_rate=preprocessing_result.sample_rate,
    )

    print(f"Postprocessing time: {postprocessing_result.postprocessing_time}")
    print(f"Piano roll shape   : {postprocessing_result.piano_roll_png_path}")
    print(f"Piano roll dtype   : {postprocessing_result.piano_roll_svg_path}")
    print(f"Probabilities shape: {postprocessing_result.midi_path}")
    print(f"Probabilities dtype: {postprocessing_result.musicxml_path}")
    print(f"Probabilities shape: {postprocessing_result.score_pdf_path}")
    print(f"Probabilities dtype: {postprocessing_result.score_svg_path}")


if __name__ == "__main__":
    main()
