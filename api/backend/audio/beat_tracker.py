import logging
from dataclasses import dataclass

import librosa
import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class BeatTrackingResult:
    """
    Result produced by beat tracking.

    Attributes:
        tempo:
            Estimated tempo in beats per minute.

        beat_frames:
            Beat positions expressed as audio frame indices.

        beat_times:
            Beat positions expressed in seconds.
    """

    tempo: float
    beat_frames: NDArray[np.int64]
    beat_times: NDArray[np.float32]


class BeatTracker:
    """
    Estimate musical beat positions from an audio waveform.

    This implementation uses librosa's dynamic-programming beat tracker.

    The detected beat grid is intended for downstream rhythmic processing,
    such as note quantization.

    Input assumptions:
        - Audio waveform is mono.
        - Audio samples are floating-point values.
        - Sample rate is expressed in Hz.
    """

    def __init__(
        self,
        hop_length: int,
    ) -> None:
        """
        Initialize beat tracker.

        Args:
            hop_length:
                Number of samples between successive analysis frames.

        Raises:
            ValueError:
                If hop_length is not strictly positive.
        """

        if hop_length <= 0:
            raise ValueError("hop_length must be strictly positive.")

        self._hop_length = hop_length

        logger.debug(
            "BeatTracker initialized: hop_length=%d",
            hop_length,
        )

    def track(
        self,
        audio: NDArray[np.float32],
        sample_rate: int,
    ) -> BeatTrackingResult:
        """
        Estimate tempo and beat positions from audio.

        Args:
            audio:
                Mono audio waveform with shape ``(n_samples,)``.

            sample_rate:
                Sampling rate of the waveform in Hz.

        Returns:
            BeatTrackingResult containing:
                - estimated tempo;
                - beat frame indices;
                - beat timestamps in seconds.

        Raises:
            ValueError:
                If audio is empty or sample_rate is invalid.
        """

        if audio.size == 0:
            raise ValueError("Audio waveform cannot be empty.")

        if sample_rate <= 0:
            raise ValueError("sample_rate must be strictly positive.")

        logger.info("Starting beat tracking.")

        logger.debug(
            "Beat tracking input: samples=%d, sample_rate=%d Hz.",
            audio.shape[0],
            sample_rate,
        )

        onset_env = librosa.onset.onset_strength(
            y=audio,
            sr=sample_rate,
            hop_length=self._hop_length,
        )

        tempo, beat_frames = librosa.beat.beat_track(
            onset_envelope=onset_env,
            sr=sample_rate,
            hop_length=self._hop_length,
        )

        tempo_value = float(np.asarray(tempo).squeeze())

        beat_frames = np.asarray(
            beat_frames,
            dtype=np.int64,
        )

        beat_times = librosa.frames_to_time(
            beat_frames,
            sr=sample_rate,
            hop_length=self._hop_length,
        ).astype(np.float32)

        logger.info(
            "Beat tracking completed: tempo=%.1f BPM, beats=%d.",
            tempo_value,
            beat_frames.size,
        )

        logger.debug(
            "Beat timestamps generated: duration=%.2f seconds.",
            float(beat_times[-1]) if beat_times.size else 0.0,
        )

        return BeatTrackingResult(
            tempo=tempo_value,
            beat_frames=beat_frames,
            beat_times=beat_times,
        )
