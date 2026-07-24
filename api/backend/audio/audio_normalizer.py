import logging
from enum import StrEnum
from typing import Any

import librosa
import numpy as np
from api.backend.type_aliases import FloatArray
from numpy.typing import NDArray

from .audio_validator import validate_audio

logger = logging.getLogger(__name__)


class NormalizationType(StrEnum):
    """Supported audio normalization strategies."""

    PEAK = "peak"
    RMS = "rms"
    PEAK_RMS = "peak+rms"
    NONE = "none"


class AudioNormalizer:
    """Normalize audio signals before feature extraction.

    This component standardizes waveform representation before DSP
    processing and model inference.

    Supported operations:

        - PCM integer to float32 conversion.
        - Multi-channel to mono conversion.
        - DC offset removal.
        - Sample rate conversion.
        - Peak normalization.
        - RMS normalization.

    Audio tensors are expected to use:

        - ``(n_samples,)`` for mono signals.
        - ``(n_channels, n_samples)`` for multi-channel signals.

    All processing assumes floating-point signals.
    """

    _EPSILON: float = 1e-9

    def to_float32(
        self,
        audio_data: NDArray[Any],
    ) -> NDArray[np.float32]:
        """Convert audio data to float32 representation.

        Integer PCM values are scaled to approximately ``[-1.0, 1.0]``.

        Args:
            audio_data:
                Input waveform.

        Returns:
            Float32 waveform.
        """

        logger.debug("Converting audio waveform to float32.")

        if np.issubdtype(audio_data.dtype, np.integer):
            info = np.iinfo(audio_data.dtype)

            scale = max(
                abs(info.min),
                info.max,
            )

            return (audio_data / scale).astype(np.float32, copy=False)

        return audio_data.astype(np.float32, copy=False)

    def to_mono(
        self,
        audio_data: FloatArray,
    ) -> FloatArray:
        """Convert multi-channel audio to mono.

        Args:
            audio_data:
                Input waveform.

        Returns:
            Mono waveform.
        """

        validate_audio(audio_data)

        if audio_data.ndim == 1:
            logger.debug("Audio already mono.")
            return audio_data

        logger.debug(
            "Converting %d channels to mono.",
            audio_data.shape[0],
        )

        return np.asarray(
            librosa.to_mono(audio_data),
            dtype=audio_data.dtype,
        )

    def remove_dc_offset(
        self,
        audio_data: FloatArray,
    ) -> FloatArray:
        """Remove constant DC component.

        Args:
            audio_data:
                Input waveform.

        Returns:
            DC corrected waveform.
        """

        validate_audio(audio_data)

        offset = float(np.mean(audio_data))

        logger.debug(
            "Removing DC offset: %.8f.",
            offset,
        )

        return audio_data - offset

    def resample(
        self,
        audio_data: FloatArray,
        sample_rate: int,
        target_sample_rate: int = 22_050,
    ) -> tuple[FloatArray, int]:
        """Resample waveform.

        Args:
            audio_data:
                Input waveform.

            sample_rate:
                Original sample rate.

            target_sample_rate:
                Desired sample rate.

        Returns:
            Tuple containing resampled waveform and new rate.

        Raises:
            ValueError:
                If sample rates are invalid.
        """

        validate_audio(audio_data)

        if sample_rate <= 0 or target_sample_rate <= 0:
            raise ValueError(
                "Sample rates must be strictly positive.",
            )

        if sample_rate == target_sample_rate:
            logger.debug("Skipping resampling.")
            return audio_data, sample_rate

        logger.debug(
            "Resampling audio: %d Hz -> %d Hz.",
            sample_rate,
            target_sample_rate,
        )

        resampled = librosa.resample(
            audio_data,
            orig_sr=sample_rate,
            target_sr=target_sample_rate,
        )

        return (
            np.asarray(resampled, dtype=audio_data.dtype),
            target_sample_rate,
        )

    def normalize_peak(
        self,
        audio_data: FloatArray,
        target_peak: float = 0.99,
    ) -> FloatArray:
        """Normalize waveform peak amplitude.

        Args:
            audio_data:
                Input waveform.

            target_peak:
                Desired maximum amplitude.

        Returns:
            Peak normalized waveform.
        """

        validate_audio(audio_data)

        if target_peak <= 0:
            raise ValueError(
                "target_peak must be positive.",
            )

        peak = float(np.max(np.abs(audio_data)))

        if peak < self._EPSILON:
            logger.warning(
                "Skipping peak normalization: signal amplitude is near zero.",
            )
            return audio_data

        gain = target_peak / peak

        logger.debug(
            "Applying peak normalization: gain=%.6f.",
            gain,
        )

        return audio_data * gain

    def normalize_rms(
        self,
        audio_data: FloatArray,
        target_rms: float = 0.1,
        clip: bool = False,
    ) -> FloatArray:
        """Normalize waveform RMS energy.

        Args:
            audio_data:
                Input waveform.

            target_rms:
                Desired RMS amplitude.

            clip:
                Clip output to [-1, 1].

        Returns:
            RMS normalized waveform.
        """

        validate_audio(audio_data)

        if target_rms <= 0:
            raise ValueError("target_rms must be positive.")

        rms = float(
            np.sqrt(np.mean(audio_data**2)),
        )

        if rms < self._EPSILON:
            logger.warning("Skipping RMS normalization: signal energy is near zero.")
            return audio_data

        gain = target_rms / rms

        logger.debug(
            "Applying RMS normalization: gain=%.6f.",
            gain,
        )

        normalized = audio_data * gain

        if clip:
            logger.debug("Clipping normalized waveform.")
            normalized = np.clip(normalized, -1.0, 1.0)

        return normalized

    def normalize(
        self,
        audio_data: FloatArray,
        normalization_type: NormalizationType,
        target_rms: float = 0.1,
        target_peak: float = 0.99,
    ) -> FloatArray:
        """Apply selected normalization strategy.

        Args:
            audio_data:
                Input waveform.

            normalization_type:
                Normalization algorithm.

            target_rms:
                RMS target.

            target_peak:
                Peak target.

        Returns:
            Normalized waveform.
        """

        validate_audio(audio_data)

        logger.debug(
            "Normalization strategy: %s.",
            normalization_type,
        )

        match normalization_type:
            case NormalizationType.NONE:
                return audio_data

            case NormalizationType.PEAK:
                return self.normalize_peak(audio_data, target_peak)

            case NormalizationType.RMS:
                return self.normalize_rms(audio_data, target_rms)

            case NormalizationType.PEAK_RMS:
                return self.normalize_rms(
                    self.normalize_peak(audio_data, target_peak),
                    target_rms,
                )

            case _:
                raise ValueError(
                    f"Unsupported normalization type: {normalization_type}",
                )
