import logging
from enum import StrEnum

import librosa
import numpy as np
from numpy.typing import NDArray

from src.transformers import AbstractTransformer
from src.utils import FloatAudioArray, validate_audio


class NormalizationType(StrEnum):
    """Supported audio normalization strategies."""

    PEAK = "peak"
    RMS = "rms"
    PEAK_RMS = "peak+rms"
    NONE = "none"


class AudioNormalizer(AbstractTransformer):
    """
    Audio preprocessing pipeline for guitar signals.

    This processor standardizes raw audio signals before feature extraction
    or model inference.

    The internal audio representation is expected to follow the shape:

        - mono: `(n_samples,)`
        - multi-channel: `(n_channels, n_samples)`

    The processor assumes floating-point audio data normalized in the
    range `[-1.0, 1.0]`.

    Processing capabilities include:
        - dtype normalization
        - mono conversion
        - DC offset removal
        - resampling
        - peak normalization
        - RMS normalization
    """

    _EPSILON: float = 1e-9

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the audio processor.

        Args:
            logger: Logger instance.
        """

        super().__init__(logger)

    def to_float32(self, audio_data: np.ndarray) -> NDArray[np.float32]:
        """Convert audio data to float32 in the range [-1.0, 1.0].

        Integer PCM formats are automatically scaled.

        Args:
            audio_data: Input audio signal.

        Returns:
            Audio signal converted to float32.
        """

        self.logger.debug("Converting audio to float32.")

        if np.issubdtype(audio_data.dtype, np.integer):
            info = np.iinfo(audio_data.dtype)
            audio_float = audio_data.astype(np.float32) / max(
                abs(info.min),
                info.max,
            )
            return audio_float

        return audio_data.astype(np.float32, copy=False)

    def to_mono(self, audio_data: FloatAudioArray) -> FloatAudioArray:
        """Convert multi-channel audio to mono.

        Multi-channel audio must follow the shape:
        `(n_channels, n_samples)`.

        Args:
            audio_data: Input audio signal.

        Returns:
            Mono audio signal.
        """

        validate_audio(audio_data)

        if audio_data.ndim == 1:
            self.logger.debug("Audio already mono.")
            return audio_data

        self.logger.debug(f"Converting {audio_data.shape[0]}-channel audio to mono.")

        return librosa.to_mono(audio_data)

    def remove_dc_offset(
        self,
        audio_data: FloatAudioArray,
    ) -> FloatAudioArray:
        """Remove DC offset from an audio signal.

        Args:
            audio_data: Input audio signal.

        Returns:
            DC-corrected audio signal.
        """
        validate_audio(audio_data)

        dc_offset = np.mean(audio_data)

        self.logger.debug(f"Removing DC offset: {dc_offset:.8f}")

        return audio_data - dc_offset

    def resample(
        self,
        audio_data: FloatAudioArray,
        sample_rate: int,
        target_sample_rate: int = 22_050,
    ) -> tuple[FloatAudioArray, int]:
        """Resample audio to the target sample rate.

        Args:
            audio_data: Input audio signal.
            sample_rate: Original sampling rate.
            target_sample_rate: Desired sampling rate.

        Returns:
            Tuple containing:
                - Resampled audio signal
                - Output sample rate

        Raises:
            ValueError: If sample rates are invalid.
        """

        validate_audio(audio_data)

        if sample_rate <= 0:
            raise ValueError("Sample rate must be strictly positive.")

        if target_sample_rate <= 0:
            raise ValueError("Target sample rate must be strictly positive.")

        if sample_rate == target_sample_rate:
            self.logger.debug("No resampling needed.")
            return audio_data, sample_rate

        self.logger.debug(
            f"Resampling audio from {sample_rate} Hz to {target_sample_rate} Hz."
        )

        resampled_audio = librosa.resample(
            audio_data,
            orig_sr=sample_rate,
            target_sr=target_sample_rate,
        )

        return resampled_audio, target_sample_rate

    def is_silent(
        self,
        audio_data: FloatAudioArray,
        threshold: float = 1e-8,
    ) -> bool:
        """Check whether an audio signal is effectively silent.

        Args:
            audio_data: Input audio signal.
            threshold: Silence detection threshold.

        Returns:
            True if the signal RMS is below the threshold.
        """

        validate_audio(audio_data)

        rms = float(np.sqrt(np.mean(audio_data**2)))

        return rms < threshold

    def normalize_peak(
        self,
        audio_data: FloatAudioArray,
        target_peak: float = 0.99,
    ) -> FloatAudioArray:
        """Apply peak normalization.

        Args:
            audio_data: Input audio signal.
            target_peak: Desired absolute peak amplitude.

        Returns:
            Peak-normalized audio signal.
        """

        validate_audio(audio_data)

        peak = float(np.max(np.abs(audio_data)))

        if peak < self._EPSILON:
            self.logger.warning(
                "Peak amplitude near zero; skipping peak normalization."
            )
            return audio_data

        gain = target_peak / peak

        self.logger.debug(f"Applying peak normalization with gain {gain:.6f}.")

        return audio_data * gain

    def normalize_rms(
        self,
        audio_data: FloatAudioArray,
        target_rms: float = 0.1,
        clip: bool = False,
    ) -> FloatAudioArray:
        """Apply RMS normalization.

        Args:
            audio_data: Input audio signal.
            target_rms: Desired RMS amplitude.
            clip: Whether to clip the output to [-1.0, 1.0].

        Returns:
            RMS-normalized audio signal.
        """

        validate_audio(audio_data)

        rms = float(np.sqrt(np.mean(audio_data**2)))

        if rms < self._EPSILON:
            self.logger.warning("RMS amplitude near zero; skipping RMS normalization.")
            return audio_data

        gain = target_rms / rms

        self.logger.debug(f"Applying RMS normalization with gain {gain:.6f}.")

        normalized_audio = audio_data * gain

        if clip:
            self.logger.debug("Clipping normalized audio to [-1.0, 1.0].")
            normalized_audio = np.clip(normalized_audio, -1.0, 1.0)

        return normalized_audio

    def normalize(
        self,
        audio_data: FloatAudioArray,
        normalization_type: NormalizationType = NormalizationType.PEAK_RMS,
        target_rms: float = 0.1,
        target_peak: float = 0.99,
    ) -> FloatAudioArray:
        """Apply a normalization strategy.

        Args:
            audio_data: Input audio signal.
            normalization_type: Selected normalization strategy.
            target_rms: RMS target value.
            target_peak: Peak target value.

        Returns:
            Normalized audio signal.

        Raises:
            ValueError: If the normalization strategy is unsupported.
        """

        validate_audio(audio_data)

        self.logger.debug(f"Selected normalization strategy: {normalization_type}")

        if normalization_type is NormalizationType.NONE:
            return audio_data

        if normalization_type is NormalizationType.PEAK:
            return self.normalize_peak(
                audio_data,
                target_peak=target_peak,
            )

        if normalization_type is NormalizationType.RMS:
            return self.normalize_rms(
                audio_data,
                target_rms=target_rms,
            )

        if normalization_type is NormalizationType.PEAK_RMS:
            peak_normalized = self.normalize_peak(
                audio_data,
                target_peak=target_peak,
            )

            return self.normalize_rms(
                peak_normalized,
                target_rms=target_rms,
            )

        raise ValueError(
            f"Unsupported normalization type: {normalization_type}",
        )
