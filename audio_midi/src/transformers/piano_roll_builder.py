import logging
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.transformers import AbstractTransformer
from src.utils import PianoRoll

from .prefix_features_target import PrefixFeaturesTarget


@dataclass(slots=True)
class MIDIPitchMapper:
    """
    Maps MIDI pitches to a reduced piano-roll index space.

    Attributes:
        midi_pitch_min (int): Minimum MIDI pitch (inclusive).
        midi_pitch_max (int): Maximum MIDI pitch (inclusive).
    """

    midi_pitch_min: int
    midi_pitch_max: int

    def __post_init__(self) -> None:
        """
        Compute the range of MIDI pitches.

        Raises:
            ValueError: If midi_min is greater than or equal to midi_max.
        """

        if self.midi_pitch_min >= self.midi_pitch_max:
            raise ValueError("midi_pitch_min must be < midi_pitch_max")

    @property
    def n_pitches(self) -> int:
        return self.midi_pitch_max - self.midi_pitch_min + 1

    def to_index(self, midi_pitch: int) -> int | None:
        """
        Convert a MIDI pitch to a piano-roll index.

        Args:
            midi_pitch (int): MIDI pitch value.

        Returns:
            int | None: Index in piano-roll space or None if out of range.
        """

        if self.midi_pitch_min <= midi_pitch <= self.midi_pitch_max:
            return midi_pitch - self.midi_pitch_min
        return None


@dataclass(slots=True)
class TimeMapper:
    """
    Maps time (seconds) to frame indices.

    Args:
        sample_rate (int): Audio sampling rate in Hz.
        hop_length (int): Hop length used in feature extraction.
    """

    sample_rate: int
    hop_length: int

    def __post_init__(self) -> None:
        """
        Compute the frame rate.

        Raises:
            ValueError: If sample_rate or hop_length is lower than or equal to 0.
        """

        if self.sample_rate <= 0:
            raise ValueError(f"sample_rate must be > 0: sample_rate={self.sample_rate}")

        if self.hop_length <= 0:
            raise ValueError(f"hop_length must be > 0: hop_length={self.hop_length}")

    @property
    def frame_rate(self) -> int:
        return self.sample_rate / self.hop_length

    def to_start_frame(self, time_sec: float) -> int:
        """Convert onset time to frame index using floor quantization.

        Args:
            time_sec: Time in seconds.

        Returns:
            Start frame index.
        """
        return int(math.floor(time_sec * self.frame_rate))

    def to_end_frame(self, time_sec: float) -> int:
        """Convert offset time to frame index using ceil quantization.

        Args:
            time_sec: Time in seconds.

        Returns:
            End frame index (exclusive).
        """
        return int(math.ceil(time_sec * self.frame_rate))


class PianoRollBuilder(AbstractTransformer):
    """
    Builds a frame-level piano-roll matrices for ML training.

    Expected DataFrame schema:
        - onset (float)
        - duration (float)
        - midi_pitch (int)

    Notes:
        Piano-roll intervals follow the semi-open convention:
        [start_frame, end_frame)

        - start_frame is inclusive
        - end_frame is exclusive

    Output:
        pd.DataFrame of shape (n_frames, n_pitches)
    """

    REQUIRED_COLUMNS: frozenset[str] = frozenset(
        {
            "onset",
            "duration",
            "midi_pitch",
        }
    )

    def __init__(
        self,
        logger: logging.Logger,
        pitch_mapper: MIDIPitchMapper,
        time_mapper: TimeMapper,
    ) -> None:
        """
        Args:
            logger (logging.Logger): Logger instance.
            pitch_mapper (PitchMapper): Maps MIDI pitches to index space.
            time_mapper (TimeMapper): Converts time into frame indices.
        """

        super().__init__(logger)
        self.pitch_mapper = pitch_mapper
        self.time_mapper = time_mapper

    def _validate_dataframe(
        self,
        df_annotations: pd.DataFrame,
    ) -> None:
        """Validate annotation DataFrame schema.

        Args:
            df_annotations: Annotation DataFrame.

        Raises:
            ValueError: If required columns are missing.
        """

        missing_columns = self.REQUIRED_COLUMNS.difference(df_annotations.columns)

        if missing_columns:
            raise ValueError(
                f"Missing required annotation columns: {sorted(missing_columns)}"
            )

        if df_annotations.empty:
            self.logger.warning("Annotation DataFrame is empty.")

    def transform(
        self,
        df_annotations: pd.DataFrame,
        n_frames: int,
    ) -> PianoRoll:
        """
        Convert annotations into a piano-roll matrix.

        Args:
            df (pd.DataFrame):
                Annotation DataFrame containing at least:
                - onset
                - duration
                - midi_pitch
            n_frames (int):
                Number of frames in the target representation.

        Returns:
            PianoRoll:
                Binary piano-roll matrix of shape
                (n_frames, n_pitches)
        """

        self._validate_dataframe(df_annotations=df_annotations)

        piano_roll: PianoRoll = np.zeros(
            (n_frames, self.pitch_mapper.n_pitches),
            dtype=np.uint8,
        )

        df = df_annotations.copy(deep=True)

        df["pitch_idx"] = df["midi_pitch"].map(self.pitch_mapper.to_index)
        df = df.dropna(subset=["pitch_idx"])
        df["pitch_idx"] = df["pitch_idx"].astype(np.int32)

        df["start_frame"] = df["onset"].map(self.time_mapper.to_start_frame)
        df["end_frame"] = (df["onset"] + df["duration"]).map(
            self.time_mapper.to_end_frame
        )

        for row in df.itertuples(index=False):
            start_frame = int(row.start_frame)
            end_frame = int(row.end_frame)
            pitch_idx = int(row.pitch_idx)

            # Clamp to valid frame range
            start_frame = max(0, min(start_frame, n_frames))
            end_frame = max(0, min(end_frame, n_frames))

            if end_frame <= start_frame:
                self.logger.debug(
                    "Skipping invalid note interval: "
                    f"start_frame={start_frame}, end_frame={end_frame}"
                )
                continue

            piano_roll[start_frame:end_frame, pitch_idx] = 1

        return self._to_dataframe(piano_roll)

    def _to_dataframe(self, piano_roll: PianoRoll) -> pd.DataFrame:
        """Convert piano-roll to DataFrame format."""

        return pd.DataFrame(
            piano_roll,
            columns=[
                f"{PrefixFeaturesTarget.TARGET.value}_{midi}"
                for midi in range(
                    self.pitch_mapper.midi_pitch_min,
                    self.pitch_mapper.midi_pitch_max + 1,
                )
            ],
        )
