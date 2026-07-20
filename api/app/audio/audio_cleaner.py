import logging
from enum import StrEnum
from time import perf_counter
from typing import Any

import librosa
import numpy as np
import scipy.signal as signal
from numpy.typing import NDArray

from .audio_validator import validate_audio

logger = logging.getLogger(__name__)


class DenoiseMethod(StrEnum):
    """Supported denoising strategies."""

    NONE = "none"
    SPECTRAL = "spectral"
    WIENER = "wiener"


class AudioCleaner:
    """Deterministic audio cleaning pipeline for transcription.

    Processing steps:

        1. High-pass filtering.
        2. Low-pass filtering.
        3. Optional denoising.
        4. Optional silence trimming.

    The pipeline preserves temporal alignment using zero-phase filters,
    which is important for onset detection and MIDI transcription.
    """

    _EPSILON: float = 1e-9

    def __init__(
        self,
        n_fft: int = 2048,
        hop_length: int = 512,
    ) -> None:
        """Initialize audio cleaner.

        Args:
            n_fft:
                FFT size used by spectral processing.

            hop_length:
                STFT hop length.
        """

        self._n_fft = n_fft
        self._hop_length = hop_length

    def highpass_filter(
        self,
        audio: NDArray[np.floating[Any]],
        sample_rate: int,
        cutoff: float = 80.0,
        filter_order: int = 6,
    ) -> NDArray[np.floating[Any]]:
        """Apply zero-phase high-pass filtering.

        Args:
            audio:
                Mono waveform.

            sample_rate:
                Sampling rate in Hz.

            cutoff:
                Frequency cutoff.

            filter_order:
                Butterworth filter order.

        Returns:
            Filtered waveform.
        """

        validate_audio(audio)

        logger.debug(
            "Applying high-pass filter: cutoff=%s Hz.",
            cutoff,
        )

        sos = signal.butter(
            N=filter_order,
            Wn=cutoff,
            btype="highpass",
            fs=sample_rate,
            output="sos",
        )

        return signal.sosfiltfilt(sos, audio)

    def lowpass_filter(
        self,
        audio: NDArray[np.floating[Any]],
        sample_rate: int,
        cutoff: float = 8000.0,
        filter_order: int = 6,
    ) -> NDArray[np.floating[Any]]:
        """Apply zero-phase low-pass filtering.

        Args:
            audio:
                Mono waveform.

            sample_rate:
                Sampling rate in Hz.

            cutoff:
                Frequency cutoff.

            filter_order:
                Butterworth filter order.

        Returns:
            Filtered waveform.
        """

        validate_audio(audio)

        logger.debug(
            "Applying low-pass filter: cutoff=%s Hz.",
            cutoff,
        )

        sos = signal.butter(
            N=filter_order,
            Wn=cutoff,
            btype="lowpass",
            fs=sample_rate,
            output="sos",
        )

        return signal.sosfiltfilt(sos, audio)

    def spectral_denoise(
        self,
        audio: NDArray[np.floating[Any]],
    ) -> NDArray[np.floating[Any]]:
        """Apply spectral masking denoising.

        Args:
            audio:
                Mono waveform.

        Returns:
            Denoised waveform.
        """

        validate_audio(audio)

        logger.debug(
            "Applying spectral denoising.",
        )

        stft = librosa.stft(
            audio,
            n_fft=self._n_fft,
            hop_length=self._hop_length,
        )

        magnitude = np.abs(stft)

        noise_profile = np.median(
            magnitude,
            axis=1,
            keepdims=True,
        )

        mask = magnitude / (magnitude + noise_profile + self._EPSILON)

        return librosa.istft(
            mask * stft,
            hop_length=self._hop_length,
        )

    def wiener_denoise(
        self,
        audio: NDArray[np.floating[Any]],
        strength: float = 1.0,
    ) -> NDArray[np.floating[Any]]:
        """Apply Wiener spectral denoising.

        Args:
            audio:
                Mono waveform.

            strength:
                Noise attenuation strength.

        Returns:
            Denoised waveform.
        """

        validate_audio(audio)

        logger.debug(
            "Applying Wiener denoising: strength=%s.",
            strength,
        )

        stft = librosa.stft(
            audio,
            n_fft=self._n_fft,
            hop_length=self._hop_length,
        )

        magnitude = np.abs(stft)

        noise_profile = np.percentile(
            magnitude,
            25,
            axis=1,
            keepdims=True,
        )

        signal_power = magnitude**2
        noise_power = noise_profile**2 * strength

        gain = signal_power / (signal_power + noise_power + self._EPSILON)

        return librosa.istft(
            gain * stft,
            hop_length=self._hop_length,
        )

    def trim_silence(
        self,
        audio: NDArray[np.floating[Any]],
        top_db: float = 40.0,
    ) -> NDArray[np.floating[Any]]:
        """Remove leading and trailing silence.

        Args:
            audio:
                Mono waveform.

            top_db:
                Silence threshold.

        Returns:
            Trimmed waveform.
        """

        validate_audio(audio)

        logger.debug(
            "Trimming silence: top_db=%s.",
            top_db,
        )

        trimmed, _ = librosa.effects.trim(
            audio,
            top_db=top_db,
        )

        return trimmed

    def clean(
        self,
        audio: NDArray[np.floating[Any]],
        sample_rate: int,
        *,
        use_highpass: bool = True,
        highpass_cutoff: float = 80.0,
        use_lowpass: bool = False,
        lowpass_cutoff: float = 8000.0,
        denoise_method: DenoiseMethod = DenoiseMethod.SPECTRAL,
        wiener_strength: float = 1.0,
        use_trim: bool = False,
        trim_db: float = 40.0,
    ) -> NDArray[np.floating[Any]]:
        """Execute complete cleaning pipeline.

        Args:
            audio:
                Input waveform.

            sample_rate:
                Sampling rate.

            use_highpass:
                Enable high-pass filtering.

            highpass_cutoff:
                High-pass cutoff frequency.

            use_lowpass:
                Enable low-pass filtering.

            lowpass_cutoff:
                Low-pass cutoff frequency.

            denoise_method:
                Selected denoising algorithm.

            wiener_strength:
                Wiener filtering strength.

            use_trim:
                Enable silence trimming.

            trim_db:
                Silence threshold.

        Returns:
            Cleaned waveform.
        """

        validate_audio(audio)

        start = perf_counter()

        logger.debug(
            "Starting audio cleaning pipeline.",
        )

        if use_highpass:
            audio = self.highpass_filter(
                audio,
                sample_rate,
                highpass_cutoff,
            )

        if use_lowpass:
            audio = self.lowpass_filter(
                audio,
                sample_rate,
                lowpass_cutoff,
            )

        if denoise_method == DenoiseMethod.SPECTRAL:
            audio = self.spectral_denoise(audio)

        elif denoise_method == DenoiseMethod.WIENER:
            audio = self.wiener_denoise(
                audio,
                strength=wiener_strength,
            )

        if use_trim:
            audio = self.trim_silence(
                audio,
                trim_db,
            )

        elapsed = perf_counter() - start

        logger.debug(
            "Audio cleaning completed in %.3f seconds.",
            elapsed,
        )

        return audio
