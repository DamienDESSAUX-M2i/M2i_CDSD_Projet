import logging
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .note_tracker import NoteEvent

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class QuantizedNoteEvent:
    """
    Musical note event aligned to a rhythmic grid.

    Attributes:
        pitch:
            MIDI pitch number.

        offset:
            Note onset position expressed in quarter notes from the
            beginning of the beat grid.

        duration:
            Note duration expressed in quarter notes.
    """

    pitch: int
    offset: float
    duration: float


class RhythmQuantizer:
    """
    Quantize note events using detected beat positions.

    The detected beats define a local tempo grid. Each interval between
    consecutive beats is mapped to one quarter note, allowing the
    quantizer to handle expressive performances with tempo variations.

    Quantization is performed by snapping note boundaries to the nearest
    rhythmic subdivision.
    """

    def __init__(
        self,
        subdivision: float = 0.25,
        min_note_duration: float = 0.25,
    ) -> None:
        """
        Initialize rhythm quantizer.

        Args:
            subdivision:
                Rhythmic grid resolution expressed in quarter notes.

                Examples:
                    1.0:
                        Quarter note resolution.

                    0.5:
                        Eighth note resolution.

                    0.25:
                        Sixteenth note resolution.

            min_note_duration:
                Minimum quantized note duration in quarter notes.

        Raises:
            ValueError:
                If parameters are invalid.
        """

        if subdivision <= 0:
            raise ValueError("subdivision must be strictly positive.")

        if min_note_duration <= 0:
            raise ValueError("min_note_duration must be strictly positive.")

        self.subdivision = subdivision
        self.min_note_duration = min_note_duration

        logger.debug(
            "RhythmQuantizer initialized: subdivision=%.3f, min_duration=%.3f.",
            subdivision,
            min_note_duration,
        )

    def quantize(
        self,
        notes: list[NoteEvent],
        beat_times: NDArray[np.float32],
    ) -> list[QuantizedNoteEvent]:
        """
        Quantize continuous note timings.

        Args:
            notes:
                Detected note events expressed in seconds.

            beat_times:
                Beat positions expressed in seconds.

        Returns:
            List of rhythmically quantized note events.

        Raises:
            ValueError:
                If beat information is insufficient or invalid.
        """

        self._validate_beats(beat_times)

        logger.info(
            "Quantizing notes: notes=%d, beats=%d.",
            len(notes),
            beat_times.size,
        )

        quantized: list[QuantizedNoteEvent] = []

        for note in notes:
            start = self._snap(self._time_to_beats(note.start_time, beat_times))

            end = self._snap(self._time_to_beats(note.end_time, beat_times))

            duration = max(end - start, self.min_note_duration)

            quantized.append(
                QuantizedNoteEvent(
                    pitch=note.pitch,
                    offset=start,
                    duration=duration,
                )
            )

        logger.info(
            "Quantization completed: output_notes=%d.",
            len(quantized),
        )

        return quantized

    def _time_to_beats(
        self,
        time: float,
        beat_times: NDArray[np.float32],
    ) -> float:
        """
        Convert a timestamp in seconds into beat-grid coordinates.

        The returned value is expressed in quarter notes where each beat
        interval corresponds to one unit.
        """

        index = np.searchsorted(beat_times, time, side="right") - 1

        index = int(np.clip(index, 0, len(beat_times) - 2))

        left = float(beat_times[index])

        right = float(beat_times[index + 1])

        interval = right - left

        if interval <= 0:
            raise ValueError("Beat timestamps must be strictly increasing.")

        position = index + (time - left) / interval

        return float(position)

    def _snap(
        self,
        beat_position: float,
    ) -> float:
        """
        Snap beat position to the configured rhythmic grid.
        """

        return float(round(beat_position / self.subdivision) * self.subdivision)

    def _validate_beats(
        self,
        beat_times: NDArray[np.float32],
    ) -> None:
        """
        Validate beat tracking output.

        Args:
            beat_times:
                Beat timestamps in seconds.

        Raises:
            ValueError:
                If beat sequence is invalid.
        """

        if beat_times.size < 2:
            raise ValueError("At least two beat positions are required.")

        if not np.all(np.diff(beat_times) > 0):
            raise ValueError("Beat timestamps must be strictly increasing.")
