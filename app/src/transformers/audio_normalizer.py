from typing import Literal, Tuple

import librosa
import numpy as np

from src.transformers import AbstractTransformer


class AudioNormalizer(AbstractTransformer):
    """
    Audio preprocessing pipeline for guitar signals.

    Steps:
        1. Convert to mono
        2. Resample to target sample rate
        3. Normalize amplitude (peak, RMS, or combined)

    Assumptions:
        - Input audio_data is a numpy array (float or int)
        - Shape: (n,) or (channels, n)
    """

    def __init__(self, target_sample_rate: int = 22050) -> None:
        """
        Args:
            target_sample_rate: Target sampling rate in Hz
        """
        super().__init__()
        self.target_sample_rate = target_sample_rate

    def to_mono(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Convert multi-channel audio to mono.

        Args:
            audio_data: Input audio signal

        Returns:
            Mono audio signal
        """
        if audio_data.ndim > 1:
            self.logger.debug("Converting audio to mono.")
            return librosa.to_mono(audio_data)

        self.logger.debug("Audio already mono.")
        return audio_data

    def resample(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Tuple[np.ndarray, int]:
        """
        Resample audio to target sample rate if needed.

        Args:
            audio_data: Input audio signal
            sample_rate: Original sample rate

        Returns:
            Tuple of (resampled audio, new sample rate)
        """
        if sample_rate != self.target_sample_rate:
            self.logger.debug(
                f"Resampling audio from {sample_rate} Hz to {self.target_sample_rate} Hz."
            )
            audio_data = librosa.resample(
                audio_data, orig_sr=sample_rate, target_sr=self.target_sample_rate
            )
            return audio_data, self.target_sample_rate

        self.logger.debug("No resampling needed.")
        return audio_data, sample_rate

    def normalize_peak(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply peak normalization (max amplitude scaling to [-1, 1]).

        Args:
            audio_data: Input audio signal

        Returns:
            Peak-normalized signal
        """
        self.logger.debug("Applying peak normalization.")
        return librosa.util.normalize(audio_data)

    def normalize_rms(
        self, audio_data: np.ndarray, target_rms: float = 0.1
    ) -> np.ndarray:
        """
        Apply RMS normalization to a target energy level.

        Args:
            audio_data: Input audio signal
            target_rms: Target RMS level

        Returns:
            RMS-normalized signal
        """
        rms: float = float(np.sqrt(np.mean(audio_data**2)))

        if rms < 1e-9:
            self.logger.warning("RMS is near zero; skipping normalization.")
            return audio_data

        gain: float = target_rms / rms
        self.logger.debug(f"Applying RMS normalization with gain={gain:.4f}")

        return audio_data * gain

    def normalize_audio(
        self,
        audio_data: np.ndarray,
        norm_type: Literal["peak", "rms", "peak+rms", "none"] = "peak",
        target_rms: float = 0.1,
    ) -> np.ndarray:
        """
        Apply selected normalization strategy.

        Args:
            audio_data: Input audio signal
            norm_type: Normalization strategy
            target_rms: Target RMS level if applicable

        Returns:
            Normalized audio signal
        """
        self.logger.debug(f"Normalization type selected: {norm_type}")

        if norm_type == "peak":
            return self.normalize_peak(audio_data)

        if norm_type == "rms":
            return self.normalize_rms(audio_data, target_rms)

        if norm_type == "peak+rms":
            audio_data = self.normalize_peak(audio_data)
            return self.normalize_rms(audio_data, target_rms)

        if norm_type == "none":
            self.logger.debug("Skipping normalization.")
            return audio_data

        raise ValueError(f"Unknown normalization type: {norm_type}")

    def normalize(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        norm_type: Literal["peak", "rms", "peak+rms", "none"] = "peak",
        target_rms: float = 0.1,
    ) -> Tuple[np.ndarray, int]:
        """
        Full preprocessing pipeline:
            1. Mono conversion
            2. Resampling
            3. Normalization

        Args:
            audio_data: Raw input audio signal
            sample_rate: Input sample rate
            norm_type: Normalization strategy
            target_rms: RMS target if applicable

        Returns:
            Tuple of (processed audio, sample rate)
        """
        self.logger.debug("Starting audio normalization pipeline.")

        audio_data = self.to_mono(audio_data)
        audio_data, sample_rate = self.resample(audio_data, sample_rate)
        audio_data = self.normalize_audio(
            audio_data, norm_type=norm_type, target_rms=target_rms
        )

        self.logger.debug("Audio normalization pipeline completed.")

        return audio_data, sample_rate
