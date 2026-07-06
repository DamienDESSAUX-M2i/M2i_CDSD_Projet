import logging
from enum import StrEnum

import librosa
import numpy as np
import scipy.signal as signal

from .audio_type import FloatAudioArray
from .audio_validator import validate_audio

logger = logging.getLogger(__name__)


class DenoiseMethod(StrEnum):
    """Supported denoising strategies."""

    NONE = "none"
    SPECTRAL = "spectral"
    WIENER = "wiener"


class AudioCleaner:
    """Deterministic audio cleaning pipeline for transcription tasks.

    This class focuses on:
        - Removing low-frequency rumble (HPF)
        - Optional high-frequency smoothing (LPF)
        - Single denoising strategy (spectral OR Wiener)
        - Optional silence trimming

    Design constraints:
        - Preserves transients (important for MIDI onset detection)
        - Avoids stacked denoising methods by default
        - Uses zero-phase filtering to avoid time shifts
    """

    _EPSILON: float = 1e-9

    def __init__(
        self,
        n_fft: int = 2048,
        hop_length: int = 512,
    ) -> None:
        """Initialize cleaner.

        Args:
            n_fft: FFT size for spectral methods.
            hop_length: Hop length for STFT.
        """

        self.n_fft = n_fft
        self.hop_length = hop_length

    def highpass_filter(
        self,
        audio: FloatAudioArray,
        sample_rate: int,
        cutoff: float = 80.0,
        filter_order: int = 6,
    ) -> FloatAudioArray:
        """Apply a zero-phase high-pass filter to remove low-frequency rumble.

        Args:
            audio: Input mono audio signal (1D float array).
            sample_rate: Sampling rate of the audio signal in Hz.
            cutoff: Cutoff frequency in Hz below which frequencies are attenuated.
            filter_order: Order of the Butterworth filter.
                Higher values produce a steeper frequency cutoff but may increase
                ringing sensitivity and numerical instability in extreme cases.

        Returns:
            High-pass filtered audio signal (same shape as input).
        """

        validate_audio(audio)

        logger.debug(f"Applying high-pass filter at {cutoff} Hz.")

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
        audio: FloatAudioArray,
        sample_rate: int,
        cutoff: float = 8000.0,
        filter_order: int = 6,
    ) -> FloatAudioArray:
        """Apply a zero-phase low-pass filter to reduce high-frequency noise.

        Args:
            audio: Input mono audio signal (1D float array).
            sample_rate: Sampling rate of the audio signal in Hz.
            cutoff: Cutoff frequency in Hz above which frequencies are attenuated.
            filter_order: Order of the Butterworth filter.
                Higher values produce a steeper frequency cutoff but may increase
                ringing sensitivity and numerical instability in extreme cases.

        Returns:
            Low-pass filtered audio signal (same shape as input).
        """

        validate_audio(audio)

        logger.debug(f"Applying low-pass filter at {cutoff} Hz")

        sos = signal.butter(
            N=filter_order,
            Wn=cutoff,
            btype="lowpass",
            fs=sample_rate,
            output="sos",
        )

        return signal.sosfiltfilt(sos, audio)

    def spectral_denoise(self, audio: FloatAudioArray) -> FloatAudioArray:
        """Apply soft spectral gating denoising.

        The method estimates a noise floor using a robust median magnitude
        spectrum and applies a soft mask in the frequency domain to preserve
        transients and reduce musical noise artifacts.

        Args:
            audio: Input mono audio signal (1D float array).

        Returns:
            Denoised audio signal reconstructed via inverse STFT.
        """

        validate_audio(audio)

        logger.debug("Applying spectral denoising (soft mask)")

        stft = librosa.stft(
            audio,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
        )

        mag = np.abs(stft)
        phase = np.exp(1j * np.angle(stft))

        noise_profile = np.median(mag, axis=1, keepdims=True)

        mask = mag / (mag + noise_profile + self._EPSILON)

        cleaned_stft = mask * mag * phase

        return librosa.istft(cleaned_stft, hop_length=self.hop_length)

    def wiener_denoise(
        self,
        audio: FloatAudioArray,
        strength: float = 1.0,
    ) -> FloatAudioArray:
        """Remove leading and trailing silence based on energy thresholding.

        Uses librosa energy-based trimming relative to peak amplitude.

        Args:
            audio: Input mono audio signal (1D float array).
            top_db: Threshold (in decibels) below reference level to consider silence.

        Returns:
            Trimmed audio signal (potentially shorter than input).
        """

        validate_audio(audio)

        logger.debug(f"Applying Wiener denoising: strength={strength}")

        stft = librosa.stft(
            audio,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
        )

        mag = np.abs(stft)

        noise_profile = np.percentile(mag, 25, axis=1, keepdims=True)

        signal_power = mag**2
        noise_power = (noise_profile**2) * strength

        gain = signal_power / (signal_power + noise_power + self._EPSILON)

        cleaned = gain * stft

        return librosa.istft(cleaned, hop_length=self.hop_length)

    def trim_silence(
        self,
        audio: FloatAudioArray,
        top_db: float = 40.0,
    ) -> FloatAudioArray:
        """Remove leading and trailing silence based on energy thresholding.

        Uses librosa energy-based trimming relative to peak amplitude.

        Args:
            audio: Input mono audio signal (1D float array).
            top_db: Threshold (in decibels) below reference level to consider silence.

        Returns:
            Trimmed audio signal (potentially shorter than input).
        """

        validate_audio(audio)

        logger.debug(f"Trimming silence: top_db={top_db}")

        trimmed, _ = librosa.effects.trim(audio, top_db=top_db)

        return trimmed

    def clean(
        self,
        audio: FloatAudioArray,
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
    ) -> FloatAudioArray:
        """Execute full deterministic audio cleaning pipeline.

        Processing order:
            1. High-pass filtering (rumble removal)
            2. Optional low-pass filtering
            3. Single denoising method (spectral or Wiener)
            4. Optional silence trimming

        Args:
            audio: Input mono audio signal (1D float array).
            sample_rate: Sampling rate of the audio signal in Hz.

            use_highpass: Whether to apply high-pass filtering.
            highpass_cutoff: High-pass cutoff frequency in Hz.

            use_lowpass: Whether to apply low-pass filtering.
            lowpass_cutoff: Low-pass cutoff frequency in Hz.

            denoise_method: Denoising strategy to apply.
                Options:
                    - SPECTRAL: soft spectral gating
                    - WIENER: Wiener filtering
                    - NONE: no denoising

            wiener_strength: Strength factor for Wiener filtering.
            use_trim: Whether to remove leading and trailing silence.
            trim_db: Silence threshold in dB for trimming.

        Returns:
            Cleaned mono audio signal as a 1D float array.

        Notes:
            - Filtering preserves signal length
            - Trimming may change signal length
            - Designed for downstream transcription tasks (e.g., MIDI inference)
        """

        validate_audio(audio)

        logger.debug("Starting audio cleaning pipeline.")

        if use_highpass:
            audio = self.highpass_filter(audio, sample_rate, highpass_cutoff)

        if use_lowpass:
            audio = self.lowpass_filter(audio, sample_rate, lowpass_cutoff)

        if denoise_method is not DenoiseMethod.NONE:
            if denoise_method is DenoiseMethod.SPECTRAL:
                audio = self.spectral_denoise(audio)

            elif denoise_method is DenoiseMethod.WIENER:
                audio = self.wiener_denoise(audio, strength=wiener_strength)

        if use_trim:
            audio = self.trim_silence(audio, top_db=trim_db)

        logger.debug("Audio cleaning completed.")

        return audio
