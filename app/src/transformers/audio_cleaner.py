import logging

import librosa
import numpy as np
import scipy.signal as signal

from src.transformers import AbstractTransformer


class AudioCleaner(AbstractTransformer):
    """
    Audio cleaning pipeline for guitar signals.

    Responsibilities:
        - Noise reduction (spectral gating baseline)
        - High-pass filtering (remove rumble)
        - Low-pass filtering (optional anti-high-frequency noise)

    This class does NOT perform normalization or feature extraction.
    """

    def __init__(
        self,
        logger: logging.Logger,
        n_fft: int = 2048,
        hop_length: int = 512,
    ) -> None:
        """
        Args:
            n_fft: FFT window size for spectral operations
            hop_length: Hop length for STFT
        """
        super().__init__(logger)
        self.n_fft = n_fft
        self.hop_length = hop_length

    def highpass_filter(
        self, audio_data: np.ndarray, sample_rate: int, cutoff: float = 80.0
    ) -> np.ndarray:
        """
        Apply a high-pass filter to remove low-frequency rumble.

        Args:
            audio_data: Input audio signal
            sample_rate: Sampling rate
            cutoff: Cutoff frequency in Hz

        Returns:
            Filtered audio signal
        """
        self.logger.debug(f"Applying high-pass filter at {cutoff} Hz.")

        sos = signal.butter(
            N=10, Wn=cutoff, btype="highpass", fs=sample_rate, output="sos"
        )
        return signal.sosfilt(sos, audio_data)

    def lowpass_filter(
        self, audio_data: np.ndarray, sample_rate: int, cutoff: float = 8000.0
    ) -> np.ndarray:
        """
        Apply a low-pass filter to remove high-frequency noise.

        Args:
            audio_data: Input audio signal
            sample_rate: Sampling rate
            cutoff: Cutoff frequency in Hz

        Returns:
            Filtered audio signal
        """
        self.logger.debug(f"Applying low-pass filter at {cutoff} Hz.")

        sos = signal.butter(
            N=10, Wn=cutoff, btype="lowpass", fs=sample_rate, output="sos"
        )
        return signal.sosfilt(sos, audio_data)

    def spectral_denoise(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Simple spectral gating noise reduction.

        Approach:
            - Estimate noise floor via median magnitude spectrum
            - Apply soft mask

        Args:
            audio_data: Input audio signal

        Returns:
            Denoised audio signal
        """
        self.logger.debug("Applying spectral denoising (baseline gating).")

        stft_matrix = librosa.stft(
            audio_data, n_fft=self.n_fft, hop_length=self.hop_length
        )

        magnitude = np.abs(stft_matrix)
        phase = np.angle(stft_matrix)

        noise_profile = np.median(magnitude, axis=1, keepdims=True)
        mask = magnitude > noise_profile

        stft_matrix_clean = magnitude * mask * np.exp(1j * phase)

        return librosa.istft(stft_matrix_clean, hop_length=self.hop_length)

    def wiener_filter(
        self,
        audio_data: np.ndarray,
        noise_reduction_factor: float = 1.0,
    ) -> np.ndarray:
        """
        Apply a simple STFT-based Wiener filter.

        Assumptions:
            - Noise is approximately stationary
            - Noise profile estimated via median spectrum

        Args:
            audio_data: Input audio signal
            noise_reduction_factor: Strength of noise suppression

        Returns:
            Denoised audio signal
        """

        self.logger.debug("Applying Wiener filtering.")

        stft_matrix = librosa.stft(
            audio_data, n_fft=self.n_fft, hop_length=self.hop_length
        )

        magnitude = np.abs(stft_matrix)

        noise_profile = np.median(magnitude, axis=1, keepdims=True)

        signal_power = magnitude**2
        noise_power = (noise_profile**2) * noise_reduction_factor

        wiener_gain = signal_power / (signal_power + noise_power + 1e-8)

        self.logger.debug(f"Wiener gain applied (factor={noise_reduction_factor}).")

        stft_matrix_filtered = wiener_gain * stft_matrix

        return librosa.istft(stft_matrix_filtered, hop_length=self.hop_length)

    def trim_silence(
        self,
        audio_data: np.ndarray,
        top_db: float = 40.0,
    ) -> np.ndarray:
        """
        Remove leading and trailing silence from audio signal.

        Uses librosa energy-based trimming.

        Args:
            audio_data: Input audio signal
            top_db: Threshold (in dB) below reference to consider as silence

        Returns:
            Trimmed audio signal
        """
        self.logger.debug(f"Trimming silence (top_db={top_db}).")

        trimmed_audio, index = librosa.effects.trim(
            audio_data,
            top_db=top_db,
        )

        self.logger.debug(
            f"Trimmed audio: original_len={len(audio_data)}, "
            f"new_len={len(trimmed_audio)}, "
            f"start={index[0]}, end={index[1]}"
        )

        return trimmed_audio

    def clean(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        use_highpass: bool = True,
        highpass_cutoff: float = 80.0,
        use_lowpass: bool = False,
        lowpass_cutoff: float = 8000.0,
        use_spectral_denoise: bool = True,
        use_wiener: bool = False,
        wiener_strength: float = 1.0,
        use_trim: bool = False,
        trim_db: float = 40.0,
    ) -> np.ndarray:
        """
        Full audio cleaning pipeline.

        Order:
            1. High-pass filter (remove low-frequency rumble)
            2. Low-pass filter (optional high-frequency smoothing)
            3. Wiener filtering (optional noise suppression)
            4. Spectral denoise (optional spectral gating)
            5. Silence trimming (optional removal of leading/trailing silence)

        Args:
            audio_data: Input audio signal
            sample_rate: Sampling rate in Hz

            use_highpass: Enable high-pass filtering
            highpass_cutoff: Cutoff frequency for high-pass filter (Hz)

            use_lowpass: Enable low-pass filtering
            lowpass_cutoff: Cutoff frequency for low-pass filter (Hz)

            use_spectral_denoise: Enable spectral gating noise reduction

            use_wiener: Enable Wiener filtering
            wiener_strength: Controls strength of noise suppression in Wiener filter

            use_trim: Enable trimming of leading and trailing silence
            trim_db: Threshold (in dB) below reference for silence detection

        Returns:
            Cleaned audio signal as a 1D numpy array (mono)

        Notes:
            - Trimming may alter signal length and temporal alignment
            - Filtering preserves signal length but modifies frequency content
        """

        self.logger.debug("Starting audio cleaning pipeline.")

        if use_highpass:
            self.logger.debug("High-pass filtering enabled.")
            audio_data = self.highpass_filter(
                audio_data, sample_rate, cutoff=highpass_cutoff
            )

        if use_lowpass:
            self.logger.debug("Low-pass filtering enabled.")
            audio_data = self.lowpass_filter(
                audio_data, sample_rate, cutoff=lowpass_cutoff
            )

        if use_wiener:
            self.logger.debug(f"Wiener filtering enabled (strength={wiener_strength}).")
            audio_data = self.wiener_filter(
                audio_data, noise_reduction_factor=wiener_strength
            )

        if use_spectral_denoise:
            self.logger.debug("Spectral denoising enabled.")
            audio_data = self.spectral_denoise(audio_data)

        if use_trim:
            self.logger.debug("Silence trimming enabled.")
            audio_data = self.trim_silence(audio_data, top_db=trim_db)

        self.logger.debug("Audio cleaning pipeline completed.")

        return audio_data
