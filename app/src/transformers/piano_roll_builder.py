from typing import Optional

import librosa
import numpy as np
import pandas as pd

from src.transformers import AbstractTransformer


class PitchMapper:
    """
    Maps MIDI pitches to a reduced piano-roll index space.

    Attributes:
        midi_min (int): Minimum MIDI pitch (inclusive).
        midi_max (int): Maximum MIDI pitch (inclusive).
    """

    def __init__(self, midi_min: int, midi_max: int) -> None:
        """
        Args:
            midi_min (int): Minimum MIDI pitch.
            midi_max (int): Maximum MIDI pitch.

        Raises:
            ValueError: If midi_min is greater than or equal to midi_max.
        """
        if midi_min >= midi_max:
            raise ValueError("midi_min must be < midi_max")

        self.midi_min = midi_min
        self.midi_max = midi_max
        self.n_pitches = self.midi_max - self.midi_min + 1

    def to_index(self, midi: int) -> Optional[int]:
        """
        Convert a MIDI pitch to a piano-roll index.

        Args:
            midi (int): MIDI pitch value.

        Returns:
            Optional[int]: Index in piano-roll space or None if out of range.
        """
        if self.midi_min <= midi <= self.midi_max:
            return midi - self.midi_min
        return None


class TimeMapper:
    """
    Converts time (seconds) into frame indices based on STFT parameters.
    """

    def __init__(self, sample_rate: int, hop_length: int) -> None:
        """
        Args:
            sample_rate (int): Audio sampling rate in Hz.
            hop_length (int): Hop length used in feature extraction.
        """
        self.sample_rate = sample_rate
        self.hop_length = hop_length

    def to_frame(self, t: float) -> int:
        """
        Convert time in seconds to frame index.

        Args:
            t (float): Time in seconds.

        Returns:
            int: Frame index.
        """
        return int(
            librosa.time_to_frames(
                t,
                sr=self.sample_rate,
                hop_length=self.hop_length,
            )
        )


class PianoRollBuilder(AbstractTransformer):
    """
    Builds a frame-level piano-roll representation from a pandas DataFrame.

    Expected DataFrame schema:
        - title (str)
        - time (float)
        - duration (float)
        - value (int MIDI pitch)

    Output:
        np.ndarray of shape (n_frames, n_pitches)
    """

    def __init__(
        self,
        pitch_mapper: PitchMapper,
        time_mapper: TimeMapper,
    ) -> None:
        """
        Args:
            pitch_mapper (PitchMapper): Maps MIDI values to index space.
            time_mapper (TimeMapper): Converts time into frame indices.
        """
        super().__init__()
        self.pitch = pitch_mapper
        self.time = time_mapper

    def transform(
        self,
        df_annotations: pd.DataFrame,
        n_frames: int,
    ) -> np.ndarray:
        """
        Convert annotations into a piano-roll matrix.

        Args:
            df (pd.DataFrame):
                Annotation DataFrame containing at least:
                - title
                - time
                - duration
                - value

            title (str):
                Audio title to filter annotations.

            n_frames (int):
                Number of frames in the target representation.

        Returns:
            np.ndarray:
                Binary piano-roll matrix of shape
                (n_frames, n_pitches)
        """

        piano_roll = np.zeros((n_frames, self.pitch.n_pitches), dtype=np.uint8)

        df_annotations["pitch_idx"] = df_annotations["value"].apply(self.pitch.to_index)
        df_annotations = df_annotations.dropna(subset=["pitch_idx"])

        df_annotations["start_f"] = df_annotations["time"].apply(self.time.to_frame)
        df_annotations["end_f"] = (
            df_annotations["time"] + df_annotations["duration"]
        ).apply(self.time.to_frame)

        for row in df_annotations.itertuples(index=False):
            start_f = int(row.start_f)
            end_f = int(row.end_f)
            pitch_idx = int(row.pitch_idx)

            if start_f >= n_frames:
                continue

            end_f = min(end_f, n_frames - 1)

            piano_roll[start_f:end_f, pitch_idx] = 1

        return self._to_dataframe(piano_roll=piano_roll)

    def _to_dataframe(self, piano_roll: np.ndarray) -> pd.DataFrame:
        return pd.DataFrame(
            data=piano_roll,
            columns=[
                f"pitch_{midi}"
                for midi in range(self.pitch.midi_min, self.pitch.midi_max + 1)
            ],
        )
