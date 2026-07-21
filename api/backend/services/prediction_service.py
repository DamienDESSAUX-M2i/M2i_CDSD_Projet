import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import soundfile as sf

from .inference_service import InferenceResult, InferenceService
from .postprocessing_service import PostprocessingResult, PostprocessingService
from .preprocessing_service import PreprocessingResult, PreprocessingService

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PredictionResult:
    """Result of the complete transcription pipeline.

    Attributes:
        processing_id: Unique identifier of the prediction process.
        preprocessing: Output of the preprocessing stage.
        inference: Output of the inference stage.
        postprocessing: Output of the post-processing stage.
    """

    processing_id: str
    preprocessing: PreprocessingResult
    inference: InferenceResult
    postprocessing: PostprocessingResult


class PredictionService:
    """Orchestrate the complete audio transcription pipeline.

    The prediction pipeline consists of the following stages:

        1. Audio loading
        2. Preprocessing
        3. Model inference
        4. Post-processing
        5. Prediction result generation

    This class contains no digital signal processing or machine learning logic.
    Its sole responsibility is coordinating the different services.
    """

    def __init__(
        self,
        preprocessing_service: PreprocessingService,
        inference_service: InferenceService,
        postprocessing_service: PostprocessingService,
    ) -> None:
        """Initialize the prediction service.

        Args:
            preprocessing_service: Audio preprocessing service.
            inference_service: Neural network inference service.
            postprocessing_service: Musical post-processing service.
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
            audio_path: Path to the input audio file.

        Returns:
            Result of the complete transcription pipeline.

        Raises:
            FileNotFoundError: If the audio file does not exist.
            RuntimeError: If an unexpected error occurs during prediction.
        """

        processing_id = str(uuid4())
        audio_path = Path(audio_path)

        logger.info(
            "Starting prediction for '%s' (processing_id=%s).",
            audio_path.name,
            processing_id,
        )

        try:
            logger.debug("Reading audio file '%s'.", audio_path)

            audio, sample_rate = sf.read(audio_path)

            logger.debug(
                "Audio loaded successfully (sample_rate=%d Hz, shape=%s).",
                sample_rate,
                audio.shape,
            )

            # soundfile returns (samples, channels)
            # librosa expects (channels, samples)
            if audio.ndim == 2:
                logger.debug("Transposing multi-channel audio.")
                audio = audio.T

            preprocessing_result = self._preprocessing.preprocess(
                audio=audio,
                sample_rate=sample_rate,
            )

            inference_result = self._inference.infer(
                features=preprocessing_result.features,
            )

            postprocessing_result = self._postprocessing.process(
                processing_id=processing_id,
                piano_roll=inference_result.piano_roll,
                audio=preprocessing_result.audio,
                sample_rate=preprocessing_result.sample_rate,
            )

        except Exception:
            logger.exception(
                "Prediction failed for '%s' (processing_id=%s).",
                audio_path.name,
                processing_id,
            )
            raise

        logger.info(
            (
                "Prediction completed for '%s' "
                "(processing_id=%s, preprocessing=%.3fs, "
                "inference=%.3fs, postprocessing=%.3fs)."
            ),
            audio_path.name,
            processing_id,
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
