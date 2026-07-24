import logging
from dataclasses import dataclass
from typing import cast

import librosa
import numpy as np
from numpy.typing import NDArray

from backend.type_aliases import FloatArray

from .audio_validator import validate_audio

logger = logging.getLogger(__name__)

FEATURE_EXTRACTOR_AUDIO_DATA_ERROR_MESSAGE = (
    "AudioFeatureExtractor requires mono audio."
)
FEATURE_EXTRACTOR_SAMPLE_RATE_ERROR_MESSAGE = "Sample rate must be strictly positive."


@dataclass(frozen=True, slots=True)
class ExtractedFeatures:
    """Container holding extracted audio feature matrices.

    Attributes:
        stft_db:
            STFT magnitude in decibel scale.

        mel_db:
            Mel spectrogram in decibel scale.

        cqt_db:
            Constant-Q transform in decibel scale.

        chroma:
            Chromagram representation.

        mfcc:
            Mel-frequency cepstral coefficients.
    """

    stft_db: FloatArray | None = None
    mel_db: FloatArray | None = None
    cqt_db: FloatArray | None = None
    chroma: FloatArray | None = None
    mfcc: FloatArray | None = None


class AudioFeatureExtractor:
    """Extract deterministic audio features for ML inference.

    The extractor generates time-aligned spectral representations.

    Supported features:

        - STFT magnitude in dB.
        - Mel spectrogram in dB.
        - Constant-Q transform in dB.
        - CQT chromagram.
        - MFCC coefficients.

    Input audio must be mono and floating point.
    """

    def __init__(
        self,
        n_fft: int = 2048,
        hop_length: int = 512,
        n_mels: int = 128,
        n_mfcc: int = 20,
        n_cqt_bins: int = 84,
        bins_per_octave: int = 12,
        cqt_fmin: float = float(librosa.note_to_hz("E2")),
        chroma_cqt_norm: int | float | None = 2,
    ) -> None:
        """Initialize feature extractor.

        Args:
            n_fft:
                FFT window size.

            hop_length:
                Hop size between frames.

            n_mels:
                Number of Mel bands.

            n_mfcc:
                Number of MFCC coefficients.

            n_cqt_bins:
                Number of CQT frequency bins.

            bins_per_octave:
                CQT bins per octave.

            cqt_fmin:
                Minimum CQT frequency.

            chroma_cqt_norm:
                Chromagram normalization mode.
        """

        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.n_mfcc = n_mfcc
        self.n_cqt_bins = n_cqt_bins
        self.bins_per_octave = bins_per_octave
        self.cqt_fmin = cqt_fmin
        self.chroma_cqt_norm = chroma_cqt_norm

    def _validate_input(
        self,
        audio_data: FloatArray,
        sample_rate: int,
    ) -> None:
        """Validate extractor inputs."""

        validate_audio(audio_data)

        if audio_data.ndim != 1:
            raise ValueError(FEATURE_EXTRACTOR_AUDIO_DATA_ERROR_MESSAGE)

        if sample_rate <= 0:
            raise ValueError(FEATURE_EXTRACTOR_SAMPLE_RATE_ERROR_MESSAGE)

    def compute_stft(
        self,
        audio_data: FloatArray,
    ) -> FloatArray:
        """Compute STFT magnitude representation.

        Args:
            audio_data:
                Mono waveform.

        Returns:
            STFT matrix in dB scale.
        """

        logger.debug(
            "Computing STFT: n_fft=%d hop_length=%d.",
            self.n_fft,
            self.hop_length,
        )

        spectrum = cast(
            NDArray[np.float32],
            librosa.stft(
                audio_data,
                n_fft=self.n_fft,
                hop_length=self.hop_length,
            ),
        )

        return cast(
            NDArray[np.float32],
            librosa.amplitude_to_db(np.abs(spectrum), ref=np.max),
        )

    def compute_mel(
        self,
        audio_data: FloatArray,
        sample_rate: int,
    ) -> FloatArray:
        """Compute Mel spectrogram.

        Args:
            audio_data:
                Mono waveform.

            sample_rate:
                Sampling rate.

        Returns:
            Mel spectrogram in dB.
        """

        logger.debug(
            "Computing Mel spectrogram: n_mels=%d.",
            self.n_mels,
        )

        mel = cast(
            NDArray[np.float32],
            librosa.feature.melspectrogram(
                y=audio_data,
                sr=sample_rate,
                n_fft=self.n_fft,
                hop_length=self.hop_length,
                n_mels=self.n_mels,
            ),
        )

        return cast(
            NDArray[np.float32],
            librosa.power_to_db(mel, ref=np.max),
        )

    def compute_cqt(
        self,
        audio_data: FloatArray,
        sample_rate: int,
    ) -> FloatArray:
        """Compute Constant-Q transform.

        Args:
            audio_data:
                Mono waveform.

            sample_rate:
                Sampling rate.

        Returns:
            CQT representation in dB.
        """

        logger.debug(
            "Computing CQT: bins=%d.",
            self.n_cqt_bins,
        )

        cqt = cast(
            NDArray[np.float32],
            librosa.cqt(
                y=audio_data,
                sr=sample_rate,
                hop_length=self.hop_length,
                n_bins=self.n_cqt_bins,
                bins_per_octave=self.bins_per_octave,
                fmin=self.cqt_fmin,
            ),
        )

        return cast(
            NDArray[np.float32],
            librosa.amplitude_to_db(np.abs(cqt), ref=np.max),
        )

    def compute_chroma(
        self,
        audio_data: FloatArray,
        sample_rate: int,
    ) -> FloatArray:
        """Compute CQT chromagram.

        Args:
            audio_data:
                Mono waveform.

            sample_rate:
                Sampling rate.

        Returns:
            Chromagram matrix.
        """

        logger.debug("Computing chromagram.")

        return cast(
            NDArray[np.float32],
            librosa.feature.chroma_cqt(
                y=audio_data,
                sr=sample_rate,
                hop_length=self.hop_length,
                bins_per_octave=self.bins_per_octave,
                norm=self.chroma_cqt_norm,
            ),
        )

    def compute_mfcc(
        self,
        audio_data: FloatArray,
        sample_rate: int,
    ) -> FloatArray:
        """Compute MFCC representation.

        Args:
            audio_data:
                Mono waveform.

            sample_rate:
                Sampling rate.

        Returns:
            MFCC matrix.
        """

        logger.debug(
            "Computing MFCC: coefficients=%d.",
            self.n_mfcc,
        )

        return cast(
            NDArray[np.float32],
            librosa.feature.mfcc(
                y=audio_data,
                sr=sample_rate,
                n_mfcc=self.n_mfcc,
                n_mels=self.n_mels,
                n_fft=self.n_fft,
                hop_length=self.hop_length,
            ),
        )

    def extract(
        self,
        audio_data: FloatArray,
        sample_rate: int,
        *,
        use_stft: bool = True,
        use_mel: bool = True,
        use_cqt: bool = True,
        use_chroma: bool = True,
        use_mfcc: bool = False,
    ) -> ExtractedFeatures:
        """Extract enabled audio features.

        Args:
            audio_data:
                Mono waveform.

            sample_rate:
                Sampling rate.

            use_stft:
                Enable STFT extraction.

            use_mel:
                Enable Mel extraction.

            use_cqt:
                Enable CQT extraction.

            use_chroma:
                Enable chromagram extraction.

            use_mfcc:
                Enable MFCC extraction.

        Returns:
            Extracted feature container.
        """

        self._validate_input(audio_data, sample_rate)

        logger.debug("Starting feature extraction.")

        return ExtractedFeatures(
            stft_db=self.compute_stft(audio_data) if use_stft else None,
            mel_db=self.compute_mel(audio_data, sample_rate) if use_mel else None,
            cqt_db=self.compute_cqt(audio_data, sample_rate) if use_cqt else None,
            chroma=self.compute_chroma(audio_data, sample_rate) if use_chroma else None,
            mfcc=self.compute_mfcc(audio_data, sample_rate) if use_mfcc else None,
        )

    def stack_features(
        self,
        features: ExtractedFeatures,
    ) -> NDArray[np.float32]:
        """Stack feature matrices into ML input format.

        Args:
            features:
                Extracted feature container.

        Returns:
            Matrix shaped ``(frames, features)``.

        Raises:
            ValueError:
                If no feature exists.
        """

        matrices: list[FloatArray] = []

        for matrix in (
            features.stft_db,
            features.mel_db,
            features.cqt_db,
            features.chroma,
            features.mfcc,
        ):
            if matrix is not None:
                matrices.append(matrix.T)

        if not matrices:
            raise ValueError("No features available for stacking.")

        stacked = np.concatenate(matrices, axis=1)

        logger.debug(
            "Feature stack created: shape=%s.",
            stacked.shape,
        )

        return cast(
            NDArray[np.float32],
            stacked.astype(np.float32, copy=False),
        )
