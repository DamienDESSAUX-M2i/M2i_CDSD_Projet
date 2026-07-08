from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .note_tracker import NoteEvent


@dataclass(frozen=True, slots=True)
class QuantizedNoteEvent:
    """Rhythmically quantized note.

    Attributes:
        pitch:
            MIDI pitch.

        offset:
            Note onset expressed in quarter notes.

        duration:
            Note duration expressed in quarter notes.
    """

    pitch: int
    offset: float
    duration: float


class RhythmQuantizer:
    """Quantize notes using detected beat positions.

    Beats define the temporal grid.

    Each interval between two consecutive beats corresponds to one
    quarter note, even if the tempo varies.

    This allows handling expressive performances with local tempo
    fluctuations.
    """

    def __init__(
        self,
        subdivision: float = 0.25,
        min_note_duration: float = 0.25,
    ) -> None:
        """
        Args:
            subdivision:
                Quantization grid expressed in quarter notes.

                1.0   -> quarter

                0.5   -> eighth

                0.25  -> sixteenth

                0.125 -> thirty-second

            min_duration:
                Minimum note duration.
        """

        self.subdivision = subdivision
        self.min_note_duration = min_note_duration

    def quantize(
        self,
        notes: list[NoteEvent],
        beat_times: NDArray[np.float32],
    ) -> list[QuantizedNoteEvent]:
        """Quantize note timings.

        Args:
            notes:
                Continuous note events.

            beat_times:
                Beat positions expressed in seconds.

        Returns:
            Quantized note events.
        """

        if len(beat_times) < 2:
            raise ValueError("At least two beat positions are required.")

        quantized: list[QuantizedNoteEvent] = []

        for note in notes:
            start = self._time_to_beats(
                note.start_time,
                beat_times,
            )

            end = self._time_to_beats(
                note.end_time,
                beat_times,
            )

            start = self._snap(start)

            end = self._snap(end)

            duration = max(
                end - start,
                self.min_note_duration,
            )

            quantized.append(
                QuantizedNoteEvent(
                    pitch=note.pitch,
                    offset=start,
                    duration=duration,
                )
            )

        return quantized

    def _time_to_beats(
        self,
        time: float,
        beat_times: NDArray[np.float32],
    ) -> float:
        """Convert seconds into beat coordinates."""

        idx = (
            np.searchsorted(
                beat_times,
                time,
                side="right",
            )
            - 1
        )

        idx = np.clip(
            idx,
            0,
            len(beat_times) - 2,
        )

        left = float(beat_times[idx])
        right = float(beat_times[idx + 1])

        alpha = (time - left) / (right - left)

        return idx + alpha

    def _snap(
        self,
        beat_position: float,
    ) -> float:
        """Snap a beat position onto the rhythmic grid."""

        return (
            round(
                beat_position / self.subdivision,
            )
            * self.subdivision
        )
