import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np
from app.audio import (
    AudioCleaner,
    AudioFeatureExtractor,
    AudioNormalizer,
    ContextWindowBuilder,
)
from app.core import ProcessingSettings
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PreprocessingResult:
    preprocessing_time: float
    audio: NDArray[np.floating[Any]]
    sample_rate: int
    features: NDArray[np.float32]


class PreprocessingService:
    """Inference preprocessing pipeline.

    This service reproduces exactly the preprocessing pipeline used during
    model training in order to guarantee identical feature generation during
    inference.

    The pipeline consists of:

    1. Audio normalization.
    2. Audio cleaning.
    3. Feature extraction.
    4. Optional temporal context window construction.
    """

    def __init__(self, settings: ProcessingSettings):
        """Initialize the preprocessing service.

        Args:
            settings: Application settings controlling every preprocessing step.
        """

        self.settings = settings

        self.normalizer = AudioNormalizer()

        self.cleaner = AudioCleaner(
            n_fft=settings.n_fft,
            hop_length=settings.hop_length,
        )

        self.extractor = AudioFeatureExtractor(
            n_fft=settings.n_fft,
            hop_length=settings.hop_length,
            n_mels=settings.n_mels,
            n_mfcc=settings.n_mfcc,
            n_cqt_bins=settings.n_cqt_bins,
            bins_per_octave=settings.bins_per_octave,
            cqt_fmin=settings.cqt_fmin,
            chroma_cqt_norm=settings.chroma_cqt_norm,
        )

        self.context_builder = ContextWindowBuilder(
            context_size=settings.context_size,
        )

    def preprocess(
        self,
        audio: NDArray[np.floating[Any]],
        sample_rate: int,
    ) -> PreprocessingResult:
        """Preprocess an audio signal before inference.

        Args:
            audio: Raw audio waveform.
            sample_rate: Sampling rate of the input waveform.

        Returns:
            Preprocessed feature matrix.

            Shape without context window:
                (n_frames, n_features)

            Shape with context window:
                (n_frames, context_window, n_features)
        """

        logger.info("Starting preprocessing...")

        t0 = perf_counter()

        audio, sample_rate = self._preprocess_audio(
            audio,
            sample_rate,
        )

        features = self._extract_features(
            audio,
            sample_rate,
        )

        features = self._build_context(features)

        preprocessing_time = perf_counter() - t0

        logger.info(
            f"Preprocessing completed in {preprocessing_time:.3f} s. Output shape={features.shape}"
        )

        return PreprocessingResult(
            preprocessing_time=preprocessing_time,
            audio=audio,
            sample_rate=sample_rate,
            features=features.astype(np.float32),
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
            Tuple containing:
                - Cleaned and normalized waveform.
                - Output sampling rate.
        """

        audio = self.normalizer.to_mono(audio)

        if self.settings.use_remove_dc_offset:
            audio = self.normalizer.remove_dc_offset(audio)

        audio, sample_rate = self.normalizer.resample(
            audio,
            sample_rate,
            self.settings.target_sample_rate,
        )

        audio = self.cleaner.clean(
            audio,
            sample_rate,
            use_highpass=self.settings.use_highpass,
            highpass_cutoff=self.settings.highpass_cutoff,
            use_lowpass=self.settings.use_lowpass,
            lowpass_cutoff=self.settings.lowpass_cutoff,
            denoise_method=self.settings.denoise_method,
            wiener_strength=self.settings.wiener_strength,
            use_trim=self.settings.use_trim,
            trim_db=self.settings.trim_db,
        )

        audio = self.normalizer.normalize(
            audio,
            normalization_type=self.settings.normalization_type,
            target_peak=self.settings.target_peak,
            target_rms=self.settings.target_rms,
        )

        if self.settings.use_to_float32:
            audio = self.normalizer.to_float32(audio)

        return audio, sample_rate

    def _extract_features(
        self,
        audio: NDArray[np.floating[Any]],
        sample_rate: int,
    ) -> NDArray[np.floating[Any]]:
        """Extract frame-wise acoustic features.

        Args:
            audio: Preprocessed mono waveform.
            sample_rate: Sampling rate.

        Returns:
            Feature matrix of shape (n_frames, n_features).
        """

        features = self.extractor.extract(
            audio,
            sample_rate,
            use_stft=self.settings.use_stft,
            use_mel=self.settings.use_mel,
            use_cqt=self.settings.use_cqt,
            use_chroma=self.settings.use_chroma,
            use_mfcc=self.settings.use_mfcc,
        )

        return self.extractor.stack_features(features=features)

    def _build_context(
        self,
        features: NDArray[np.floating[Any]],
    ) -> NDArray[np.float32]:
        """Construct temporal context windows.

        If context windows are disabled, the original feature matrix is returned
        unchanged.

        Args:
            features: Feature matrix of shape (n_frames, n_features).

        Returns:
            Either:

            - (n_frames, n_features)
            - (n_frames, context_window, n_features)
        """

        if not self.settings.use_context_window:
            return features

        return self.context_builder.build_context_windows(features)
