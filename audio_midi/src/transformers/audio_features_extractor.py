import logging

import librosa
import numpy as np
import pandas as pd

from src.transformers import AbstractTransformer


class AudioFeatureExtractor(AbstractTransformer):
    """
    Feature extraction pipeline for guitar audio signals.

    Extracted features:
        - STFT (dB)
        - Mel spectrogram (dB)
        - CQT (dB)
        - Chromagram
        - MFCC

    This class assumes:
        - audio is already normalized and cleaned
        - mono signal
    """

    def __init__(
        self,
        logger: logging.Logger,
        n_fft: int = 2048,  # 4096 ?
        hop_length: int = 512,  # 256 ?
        n_mels: int = 128,
        n_mfcc: int = 13,
        n_cqt_bins: int = 84,  # 88 ?
        bins_per_octave: int = 12,
        fmin: float = librosa.note_to_hz("E2"),  # C2 ?
    ) -> None:
        """
        Args:
            n_fft: FFT window size
            hop_length: Hop length
            n_mels: Number of Mel bands
            n_mfcc: Number of MFCC coefficients
            n_cqt_bins: Number of CQT bins
            bins_per_octave: Frequency resolution of CQT
            fmin: Minimum frequency for CQT
        """
        super().__init__(logger)

        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.n_mfcc = n_mfcc
        self.n_cqt_bins = n_cqt_bins
        self.bins_per_octave = bins_per_octave
        self.fmin = fmin

    def compute_stft(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Compute STFT magnitude in dB scale.

        Args:
            audio_data: Input audio signal

        Returns:
            STFT spectrogram (dB)
        """
        self.logger.debug("Computing STFT.")
        stft = np.abs(
            librosa.stft(audio_data, n_fft=self.n_fft, hop_length=self.hop_length)
        )
        return librosa.amplitude_to_db(stft, ref=np.max)

    def compute_mel(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Compute Mel spectrogram in dB scale.

        Args:
            audio_data: Input audio signal
            sample_rate: Sampling rate

        Returns:
            Mel spectrogram (dB)
        """
        self.logger.debug("Computing Mel spectrogram.")
        mel_spectrogram = librosa.feature.melspectrogram(
            y=audio_data,
            sr=sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels,
        )
        return librosa.power_to_db(mel_spectrogram, ref=np.max)

    def compute_cqt(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Compute Constant-Q Transform in dB scale.

        Args:
            audio_data: Input audio signal
            sample_rate: Sampling rate

        Returns:
            CQT spectrogram (dB)
        """
        self.logger.debug("Computing CQT.")
        cqt = np.abs(
            librosa.cqt(
                audio_data,
                sr=sample_rate,
                hop_length=self.hop_length,
                n_bins=self.n_cqt_bins,
                bins_per_octave=self.bins_per_octave,
                fmin=self.fmin,
            )
        )
        return librosa.amplitude_to_db(cqt, ref=np.max)

    def compute_chromagram(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> np.ndarray:
        """
        Compute chromagram using CQT.

        Args:
            audio_data: Input audio signal
            sample_rate: Sampling rate

        Returns:
            Chromagram (12 pitch classes)
        """
        self.logger.debug("Computing chromagram.")
        return librosa.feature.chroma_cqt(
            y=audio_data,
            sr=sample_rate,
            hop_length=self.hop_length,
            bins_per_octave=self.bins_per_octave,
        )

    def compute_mfcc(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Compute Mel-Frequency Cepstral Coefficients (MFCC).

        Args:
            audio_data: Input audio signal
            sample_rate: Sampling rate

        Returns:
            MFCC matrix (n_mfcc x time)
        """
        self.logger.debug("Computing MFCC.")
        mfcc = librosa.feature.mfcc(
            y=audio_data,
            sr=sample_rate,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
        )
        return mfcc

    def extract_features(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        use_stft: bool = True,
        use_mel: bool = True,
        use_cqt: bool = True,
        use_chroma: bool = True,
        use_mfcc: bool = False,
    ) -> pd.DataFrame:
        """
        Extract selected audio features independently.

        Each feature can be enabled/disabled via boolean flags.

        Args:
            audio_data: Input audio signal
            sample_rate: Sampling rate
            use_stft: Compute STFT (dB)
            use_mel: Compute Mel spectrogram (dB)
            use_cqt: Compute CQT (dB)
            use_chroma: Compute chromagram
            use_mfcc: Compute MFCC

        Returns:
            Dictionary mapping feature names to numpy arrays
        """

        self.logger.debug("Starting feature extraction.")

        output: dict[str, np.ndarray] = {}

        if not any([use_stft, use_mel, use_cqt, use_chroma, use_mfcc]):
            self.logger.warning("No features selected. Returning empty dictionary.")
            return output

        if use_stft:
            self.logger.debug("STFT enabled.")
            output["stft_db"] = self.compute_stft(audio_data)

        if use_mel:
            self.logger.debug("Mel spectrogram enabled.")
            output["mel_db"] = self.compute_mel(audio_data, sample_rate)

        if use_cqt:
            self.logger.debug("CQT enabled.")
            output["cqt_db"] = self.compute_cqt(audio_data, sample_rate)

        if use_chroma:
            self.logger.debug("Chromagram enabled.")
            output["chroma"] = self.compute_chromagram(audio_data, sample_rate)

        if use_mfcc:
            self.logger.debug("MFCC enabled.")
            output["mfcc"] = self.compute_mfcc(audio_data, sample_rate)

        self.logger.debug(
            f"Feature extraction completed. Extracted: {list(output.keys())}"
        )

        return self._to_dataframe(output=output)

    def _to_dataframe(self, output: dict[str, np.ndarray]) -> pd.DataFrame:
        dfs: list[pd.DataFrame] = []

        for feature_name, matrix in output.items():
            matrix = matrix.T
            dfs.append(
                pd.DataFrame(
                    data=matrix,
                    columns=[f"{feature_name}_{k}" for k in range(matrix.shape[1])],
                )
            )

        return pd.concat(dfs, axis=1)
