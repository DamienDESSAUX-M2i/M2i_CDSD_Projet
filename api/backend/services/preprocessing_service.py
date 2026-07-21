import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np
from numpy.typing import NDArray

from backend.audio import (
    AudioCleaner,
    AudioFeatureExtractor,
    AudioNormalizer,
    ContextWindowBuilder,
)
from backend.core import ProcessingSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PreprocessingResult:
    """Result of the preprocessing pipeline.

    Attributes:
        preprocessing_time: Total preprocessing time in seconds.
        audio: Preprocessed waveform.
        sample_rate: Sampling rate of the preprocessed waveform.
        features: Feature matrix ready for inference.
    """

    preprocessing_time: float
    audio: NDArray[np.floating[Any]]
    sample_rate: int
    features: NDArray[np.float32]


class PreprocessingService:
    """Preprocess audio before model inference.

    This service reproduces the preprocessing pipeline used during model
    training to guarantee identical feature generation during inference.

    The pipeline consists of:

        1. Audio normalization.
        2. Audio cleaning.
        3. Feature extraction.
        4. Optional temporal context window construction.
    """

    def __init__(
        self,
        settings: ProcessingSettings,
    ) -> None:
        """Initialize the preprocessing service.

        Args:
            settings: Processing configuration.
        """

        self._settings = settings

        self._normalizer = AudioNormalizer()

        self._cleaner = AudioCleaner(
            n_fft=settings.n_fft,
            hop_length=settings.hop_length,
        )

        self._extractor = AudioFeatureExtractor(
            n_fft=settings.n_fft,
            hop_length=settings.hop_length,
            n_mels=settings.n_mels,
            n_mfcc=settings.n_mfcc,
            n_cqt_bins=settings.n_cqt_bins,
            bins_per_octave=settings.bins_per_octave,
            cqt_fmin=settings.cqt_fmin,
            chroma_cqt_norm=settings.chroma_cqt_norm,
        )

        self._context_builder = ContextWindowBuilder(
            context_size=settings.context_size,
        )

    def preprocess(
        self,
        audio: NDArray[np.floating[Any]],
        sample_rate: int,
    ) -> PreprocessingResult:
        """Run the complete preprocessing pipeline.

        Args:
            audio: Raw audio waveform.
            sample_rate: Sampling rate of the input waveform.

        Returns:
            Result of the preprocessing pipeline.
        """

        logger.info("Starting audio preprocessing.")

        logger.debug(
            "Input audio: sample_rate=%d Hz, shape=%s.",
            sample_rate,
            audio.shape,
        )

        start_time = perf_counter()

        audio, sample_rate = self._preprocess_audio(
            audio=audio,
            sample_rate=sample_rate,
        )

        features = self._extract_features(
            audio=audio,
            sample_rate=sample_rate,
        )

        features = self._build_context(features)

        preprocessing_time = perf_counter() - start_time

        logger.info(
            "Audio preprocessing completed in %.3f s.",
            preprocessing_time,
        )

        logger.debug(
            "Preprocessing output: audio_shape=%s, features_shape=%s.",
            audio.shape,
            features.shape,
        )

        return PreprocessingResult(
            preprocessing_time=preprocessing_time,
            audio=audio,
            sample_rate=sample_rate,
            features=features.astype(np.float32, copy=False),
        )

    def _preprocess_audio(
        self,
        audio: NDArray[np.floating[Any]],
        sample_rate: int,
    ) -> tuple[NDArray[np.floating[Any]], int]:
        """Apply deterministic audio preprocessing.

        Args:
            audio: Raw audio waveform.
            sample_rate: Input sampling rate.

        Returns:
            Tuple containing the processed waveform and its sampling rate.
        """

        logger.debug("Converting audio to mono.")
        audio = self._normalizer.to_mono(audio)

        if self._settings.use_remove_dc_offset:
            logger.debug("Removing DC offset.")
            audio = self._normalizer.remove_dc_offset(audio)

        logger.debug(
            "Resampling audio from %d Hz to %d Hz.",
            sample_rate,
            self._settings.target_sample_rate,
        )

        audio, sample_rate = self._normalizer.resample(
            audio,
            sample_rate,
            self._settings.target_sample_rate,
        )

        logger.debug("Cleaning audio signal.")

        audio = self._cleaner.clean(
            audio,
            sample_rate,
            use_highpass=self._settings.use_highpass,
            highpass_cutoff=self._settings.highpass_cutoff,
            use_lowpass=self._settings.use_lowpass,
            lowpass_cutoff=self._settings.lowpass_cutoff,
            denoise_method=self._settings.denoise_method,
            wiener_strength=self._settings.wiener_strength,
            use_trim=self._settings.use_trim,
            trim_db=self._settings.trim_db,
        )

        logger.debug("Normalizing audio.")

        audio = self._normalizer.normalize(
            audio,
            normalization_type=self._settings.normalization_type,
            target_peak=self._settings.target_peak,
            target_rms=self._settings.target_rms,
        )

        if self._settings.use_to_float32:
            logger.debug("Converting waveform to float32.")
            audio = self._normalizer.to_float32(audio)

        return audio, sample_rate

    def _extract_features(
        self,
        audio: NDArray[np.floating[Any]],
        sample_rate: int,
    ) -> NDArray[np.floating[Any]]:
        """Extract acoustic features from an audio waveform.

        Args:
            audio: Preprocessed mono waveform.
            sample_rate: Waveform sampling rate.

        Returns:
            Feature matrix of shape ``(n_frames, n_features)``.
        """

        logger.debug("Extracting acoustic features.")

        features = self._extractor.extract(
            audio,
            sample_rate,
            use_stft=self._settings.use_stft,
            use_mel=self._settings.use_mel,
            use_cqt=self._settings.use_cqt,
            use_chroma=self._settings.use_chroma,
            use_mfcc=self._settings.use_mfcc,
        )

        stacked_features = self._extractor.stack_features(features)

        logger.debug(
            "Feature extraction completed: shape=%s.",
            stacked_features.shape,
        )

        return stacked_features

    def _build_context(
        self,
        features: NDArray[np.float32],
    ) -> NDArray[np.float32]:
        """Build temporal context windows.

        Args:
            features: Frame-wise feature matrix.

        Returns:
            Feature tensor with shape:

            Without context:
                (n_frames, n_features)

            With context:
                (n_frames, context_window, n_features, 1)
        """

        if not self._settings.use_context_window:
            logger.debug("Context window disabled.")
            return features.astype(np.float32, copy=False)

        logger.debug(
            "Building context windows (context_size=%d).",
            self._settings.context_size,
        )

        contextual_features = self._context_builder.build_context_windows(
            features,
        )

        logger.debug(
            "Context windows built: shape=%s.",
            contextual_features.shape,
        )

        return contextual_features.astype(np.float32, copy=False)
