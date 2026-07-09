import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import soundfile as sf

from services import (
    InferenceResult,
    InferenceService,
    PostprocessingResult,
    PostprocessingService,
    PreprocessingResult,
    PreprocessingService,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PredictionResult:
    """Result of the complete transcription pipeline.

    Attributes:
        processing_id:
            Tracking process.

        preprocessing:
            Output of the preprocessing stage.

        inference:
            Output of the inference stage.

        postprocessing:
            Output of the post-processing stage.
    """

    processing_id: str
    preprocessing: PreprocessingResult
    inference: InferenceResult
    postprocessing: PostprocessingResult


class PredictionService:
    """High-level orchestration service for audio transcription.

    This service coordinates the complete inference pipeline:

        1. Audio file
        2. PreprocessingService
        3. InferenceService
        4. PostprocessingService
        5. PredictionResult

    The class intentionally contains no DSP or machine-learning logic.
    Its sole responsibility is orchestrating the different services.
    """

    def __init__(
        self,
        preprocessing_service: PreprocessingService,
        inference_service: InferenceService,
        postprocessing_service: PostprocessingService,
    ) -> None:
        """Initialize the prediction pipeline.

        Args:
            preprocessing_service:
                Audio preprocessing service.

            inference_service:
                Neural-network inference service.

            postprocessing_service:
                Musical post-processing service.
        """

        self._preprocessing = preprocessing_service
        self._inference = inference_service
        self._postprocessing = postprocessing_service

    def predict(
        self,
        audio_path: str | Path,
    ) -> PredictionResult:
        """Run the complete transcription pipeline.

        Args:
            audio_path:
                Path to an input WAV file.

        Returns:
            Complete prediction result containing preprocessing,
            inference and post-processing outputs.

        Raises:
            FileNotFoundError:
                If the audio file does not exist.
        """

        processing_id = str(uuid4())

        audio_path = Path(audio_path)

        logger.info(
            f"Starting prediction for '{audio_path.name}': processing_id={processing_id}."
        )

        audio, sample_rate = sf.read(audio_path)

        # soundfile returns (samples, channels)
        # librosa expects (channels, samples)
        if audio.ndim == 2:
            audio = audio.T

        preprocessing_result = self._preprocessing.preprocess(
            processing_id=processing_id,
            audio=audio,
            sample_rate=sample_rate,
        )

        inference_result = self._inference.infer(
            processing_id=processing_id,
            features=preprocessing_result.features,
        )

        postprocessing_result = self._postprocessing.process(
            processing_id=processing_id,
            piano_roll=inference_result.piano_roll,
            audio=preprocessing_result.audio,
            sample_rate=preprocessing_result.sample_rate,
        )

        logger.info(
            (
                "Prediction completed "
                "(preprocessing=%.3fs, "
                "inference=%.3fs, "
                "postprocessing=%.3fs)."
            ),
            preprocessing_result.preprocessing_time,
            inference_result.inference_time,
            postprocessing_result.postprocessing_time,
        )

        return PredictionResult(
            processing_id=processing_id,
            preprocessing=preprocessing_result,
            inference=inference_result,
            postprocessing=postprocessing_result,
        )
