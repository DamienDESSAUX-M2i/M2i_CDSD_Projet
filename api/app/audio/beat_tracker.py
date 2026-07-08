import logging
from dataclasses import dataclass

import librosa
import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class BeatTrackingResult:
    """Result of beat tracking.

    Attributes:
        tempo:
            Estimated tempo in BPM.

        beat_frames:
            Beat indices expressed in spectrogram frames.

        beat_times:
            Beat positions expressed in seconds.
    """

    tempo: float
    beat_frames: NDArray[np.int64]
    beat_times: NDArray[np.float32]


class BeatTracker:
    """Estimate musical beats from an audio signal.

    This implementation relies on librosa's dynamic programming beat tracker.

    The returned beat positions are later used by the rhythm quantizer.
    """

    def __init__(
        self,
        hop_length: int,
    ) -> None:
        self.hop_length = hop_length

    def track(
        self,
        audio: NDArray[np.float32],
        sample_rate: int,
    ) -> BeatTrackingResult:
        """Estimate beats from an audio signal.

        Args:
            audio:
                Mono waveform.

            sample_rate:
                Sampling rate.

        Returns:
            BeatTrackingResult.
        """

        logger.info("Estimating tempo and beats.")

        onset_env = librosa.onset.onset_strength(
            y=audio,
            sr=sample_rate,
            hop_length=self.hop_length,
        )

        tempo, beat_frames = librosa.beat.beat_track(
            onset_envelope=onset_env,
            sr=sample_rate,
            hop_length=self.hop_length,
        )

        beat_times = librosa.frames_to_time(
            beat_frames,
            sr=sample_rate,
            hop_length=self.hop_length,
        ).astype(np.float32)

        logger.info(
            f"Beat tracking completed: {float(tempo):.1f} BPM ({len(beat_frames)} beats)."
        )

        return BeatTrackingResult(
            tempo=float(tempo),
            beat_frames=beat_frames.astype(np.int64),
            beat_times=beat_times,
        )
