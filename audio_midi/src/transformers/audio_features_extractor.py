import logging
from dataclasses import dataclass

import librosa
import numpy as np
import pandas as pd

from src.transformers import AbstractTransformer
from src.utils import FeatureMatrix, FloatAudioArray, validate_audio


@dataclass(slots=True)
class ExtractedFeatures:
    """Container for raw extracted feature matrices.

    This structure holds time-aligned feature matrices before conversion
    into tabular format.

    Attributes:
        stft_db: STFT magnitude in decibel scale, shape (freq_bins, time_frames).
        mel_db: Mel spectrogram in decibel scale, shape (mel_bins, time_frames).
        cqt_db: Constant-Q transform in decibel scale, shape (cqt_bins, time_frames).
        chroma: Chromagram (12 pitch classes), shape (12, time_frames).
        mfcc: MFCC coefficients, shape (n_mfcc, time_frames).
    """

    stft_db: FeatureMatrix | None = None
    mel_db: FeatureMatrix | None = None
    cqt_db: FeatureMatrix | None = None
    chroma: FeatureMatrix | None = None
    mfcc: FeatureMatrix | None = None


class AudioFeatureExtractor(AbstractTransformer):
    """Deterministic feature extraction for audio ML pipelines.

    This class extracts multiple time-frequency representations from mono audio
    signals and ensures temporal alignment across features using a shared hop length.

    Extracted representations include:
        - STFT (log-magnitude in dB)
        - Mel spectrogram (power in dB)
        - Constant-Q Transform (log-magnitude in dB)
        - Chromagram (pitch class energy)
        - MFCC (cepstral coefficients)

    Assumptions:
        - Input audio is mono and already validated
        - Sampling rate is consistent across all calls
        - Features are aligned along time axis (frame axis)
    """

    def __init__(
        self,
        logger: logging.Logger,
        n_fft: int = 2048,
        hop_length: int = 512,
        n_mels: int = 128,
        n_mfcc: int = 20,
        n_cqt_bins: int = 84,
        bins_per_octave: int = 12,
        cqt_fmin: float = librosa.note_to_hz("E2"),
        chroma_cqt_norm: int | float | None = 2,
    ) -> None:
        super().__init__(logger)
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.n_mfcc = n_mfcc
        self.n_cqt_bins = n_cqt_bins
        self.bins_per_octave = bins_per_octave
        self.cqt_fmin = cqt_fmin
        self.chroma_cqt_norm = chroma_cqt_norm

    def compute_stft(self, audio_data: FloatAudioArray) -> FeatureMatrix:
        """Compute Short-Time Fourier Transform (STFT) magnitude in dB scale.

        The STFT is computed using a Hann window with configurable FFT size and hop length.
        Output is converted to log-amplitude scale for numerical stability.

        Args:
            audio_data: Input mono audio signal (1D float array).

        Returns:
            STFT spectrogram in decibel scale with shape (freq_bins, time_frames).
        """

        self.logger.debug("Computing STFT.")
        stft = librosa.stft(
            audio_data,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            center=True,
        )
        return librosa.amplitude_to_db(np.abs(stft), ref=np.max)

    def compute_mel(
        self, audio_data: FloatAudioArray, sample_rate: int
    ) -> FeatureMatrix:
        """Compute Mel-scaled spectrogram in dB scale.

        The Mel spectrogram is computed from a power spectrogram and mapped
        onto a perceptual frequency scale.

        Args:
            audio_data: Input mono audio signal (1D float array).
            sample_rate: Sampling rate of the audio signal in Hz.

        Returns:
            Mel spectrogram in dB scale with shape (mel_bins, time_frames).
        """

        self.logger.debug("Computing Mel spectrogram.")
        mel = librosa.feature.melspectrogram(
            y=audio_data,
            sr=sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels,
            center=True,
        )
        return librosa.power_to_db(mel, ref=np.max)

    def compute_cqt(
        self, audio_data: FloatAudioArray, sample_rate: int
    ) -> FeatureMatrix:
        """Compute Constant-Q Transform (CQT) in dB scale.

        The CQT provides a logarithmic frequency resolution aligned with musical pitch.

        Args:
            audio_data: Input mono audio signal (1D float array).
            sample_rate: Sampling rate of the audio signal in Hz.

        Returns:
            CQT spectrogram in dB scale with shape (cqt_bins, time_frames).
        """

        self.logger.debug("Computing CQT.")
        cqt = librosa.cqt(
            audio_data,
            sr=sample_rate,
            hop_length=self.hop_length,
            n_bins=self.n_cqt_bins,
            bins_per_octave=self.bins_per_octave,
            fmin=self.cqt_fmin,
        )
        return librosa.amplitude_to_db(np.abs(cqt), ref=np.max)

    def compute_chroma(
        self, audio_data: FloatAudioArray, sample_rate: int
    ) -> FeatureMatrix:
        """Compute chromagram using Constant-Q Transform (CQT).

        The chromagram represents energy distribution across the 12 pitch classes.

        Args:
            audio_data: Input mono audio signal (1D float array).
            sample_rate: Sampling rate of the audio signal in Hz.

        Returns:
            Chromagram with shape (12, time_frames).
        """

        self.logger.debug("Computing chroma.")
        return librosa.feature.chroma_cqt(
            y=audio_data,
            sr=sample_rate,
            hop_length=self.hop_length,
            bins_per_octave=self.bins_per_octave,
            norm=self.chroma_cqt_norm,
        )

    def compute_mfcc(
        self, audio_data: FloatAudioArray, sample_rate: int
    ) -> FeatureMatrix:
        """Compute Mel-Frequency Cepstral Coefficients (MFCCs).

        MFCCs represent a compressed spectral envelope using a DCT over Mel bands.

        Args:
            audio_data: Input mono audio signal (1D float array).
            sample_rate: Sampling rate of the audio signal in Hz.

        Returns:
            MFCC matrix with shape (n_mfcc, time_frames).
        """

        self.logger.debug("Computing MFCC.")
        return librosa.feature.mfcc(
            y=audio_data,
            sr=sample_rate,
            n_mfcc=self.n_mfcc,
            n_mels=self.n_mels,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            center=True,
        )

    def extract(
        self,
        audio_data: FloatAudioArray,
        sample_rate: int,
        *,
        use_stft: bool = True,
        use_mel: bool = True,
        use_cqt: bool = True,
        use_chroma: bool = True,
        use_mfcc: bool = False,
    ) -> pd.DataFrame:
        """Extract multiple time-aligned audio features.

        Each feature extraction can be enabled or disabled independently.

        Args:
            audio_data: Input mono audio signal (1D float array).
            sample_rate: Sampling rate of the audio signal in Hz.
            use_stft: Whether to compute STFT features.
            use_mel: Whether to compute Mel spectrogram features.
            use_cqt: Whether to compute CQT features.
            use_chroma: Whether to compute chromagram features.
            use_mfcc: Whether to compute MFCC features.

        Returns:
            pd.DataFrame containing extracted features.
        """

        validate_audio(audio_data)

        self.logger.debug("Starting feature extraction.")

        return self._to_dataframe(
            ExtractedFeatures(
                stft_db=self.compute_stft(audio_data) if use_stft else None,
                mel_db=self.compute_mel(audio_data, sample_rate) if use_mel else None,
                cqt_db=self.compute_cqt(audio_data, sample_rate) if use_cqt else None,
                chroma=self.compute_chroma(audio_data, sample_rate)
                if use_chroma
                else None,
                mfcc=self.compute_mfcc(audio_data, sample_rate) if use_mfcc else None,
            )
        )

    def _to_dataframe(self, features: ExtractedFeatures) -> pd.DataFrame:
        """Convert extracted feature matrices into a unified pandas DataFrame.

        Each feature matrix is transposed so that rows correspond to time frames
        and columns correspond to feature dimensions. All feature sets are
        concatenated along the feature axis.

        Args:
            features: Container holding extracted feature matrices.

        Returns:
            Pandas DataFrame of shape (time_frames, total_feature_dimensions).
            Returns an empty DataFrame if no features are provided.
        """

        def to_df(mat: FeatureMatrix | None, name: str) -> pd.DataFrame | None:
            if mat is None:
                return None

            mat_t = mat.T  # (time, features)

            return pd.DataFrame(
                mat_t,
                columns=[f"{name}_{i}" for i in range(mat_t.shape[1])],
            )

        dfs = [
            df
            for df in [
                to_df(features.stft_db, "stft"),
                to_df(features.mel_db, "mel"),
                to_df(features.cqt_db, "cqt"),
                to_df(features.chroma, "chroma"),
                to_df(features.mfcc, "mfcc"),
            ]
            if df is not None
        ]

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs, axis=1)
