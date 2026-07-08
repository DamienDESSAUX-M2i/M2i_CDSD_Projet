import logging
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class NoteEvent:
    """Represents a detected musical note."""

    pitch: int
    start_time: float
    end_time: float
    velocity: int = 100

    @property
    def duration(self) -> float:
        """Return note duration in seconds."""
        return self.end_time - self.start_time


class NoteTracker:
    """Convert frame-wise piano rolls into musical note events.

    The model output is expected to be a binary piano roll:

        shape = (frames, pitches)

    where each column corresponds to a MIDI pitch.

    Notes are reconstructed by grouping consecutive active frames.

    Example:

        Frame activation:

        [
            [0,1],
            [0,1],
            [0,1],
            [0,0],
        ]

        becomes:

        Note(
            pitch=41,
            start_time=0,
            end_time=3 * frame_duration
        )

    Args:
        hop_length:
        sample_rate:
        midi_pitch_min:
        midi_pitch_max:
        min_note_duration:
        velocity:
    """

    def __init__(
        self,
        hop_length: int = 512,
        sample_rate: int = 22050,
        midi_pitch_min: int = 40,
        midi_pitch_max: int = 88,
        min_note_duration: float = 0.02,
        velocity: int = 100,
    ) -> None:

        self.hop_length = hop_length
        self.sample_rate = sample_rate
        self.midi_pitch_min = midi_pitch_min
        self.midi_pitch_max = midi_pitch_max
        self.min_note_duration = min_note_duration
        self.velocity = velocity
        self.frame_duration = self.hop_length / self.sample_rate

    def extract_notes(
        self,
        piano_roll: NDArray[np.bool_],
    ) -> list[NoteEvent]:
        """Extract note events from a binary piano roll.

        Args:
            piano_roll:
                Binary matrix with shape:

                    (n_frames, n_pitches)

        Returns:
            List of detected notes.
        """

        self._validate_piano_roll(piano_roll)

        notes: list[NoteEvent] = []

        n_frames, n_pitches = piano_roll.shape

        logger.info(
            f"Tracking notes from piano roll ({n_frames} frames, {n_pitches} pitches)."
        )

        for pitch_idx in range(n_pitches):
            pitch = self.midi_pitch_min + pitch_idx

            activations = piano_roll[:, pitch_idx]

            notes.extend(self._extract_pitch_notes(activations, pitch))

        logger.info(f"Detected {len(notes)} notes.")

        return notes

    def _extract_pitch_notes(
        self,
        activations: NDArray[np.bool_],
        pitch: int,
    ) -> list[NoteEvent]:
        """Extract consecutive activations for one pitch."""

        notes: list[NoteEvent] = []

        start_frame: int | None = None

        for frame, active in enumerate(activations):
            if active and start_frame is None:
                start_frame = frame

            elif not active and start_frame is not None:
                notes.append(self._create_note(pitch, start_frame, frame))

                start_frame = None

        # Handle note reaching end of sequence
        if start_frame is not None:
            notes.append(self._create_note(pitch, start_frame, len(activations)))

        return [note for note in notes if note.duration >= self.min_note_duration]

    def _create_note(
        self,
        pitch: int,
        start_frame: int,
        end_frame: int,
    ) -> NoteEvent:
        """Create note from frame boundaries."""

        return NoteEvent(
            pitch=pitch,
            start_time=(start_frame * self.frame_duration),
            end_time=(end_frame * self.frame_duration),
            velocity=self.velocity,
        )

    def _validate_piano_roll(
        self,
        piano_roll: NDArray[np.bool_],
    ) -> None:
        """Validate piano roll dimensions."""

        if piano_roll.ndim != 2:
            raise ValueError("Piano roll must have shape (frames, pitches).")

        expected_pitches = self.midi_pitch_max - self.midi_pitch_min + 1

        if piano_roll.shape[1] != expected_pitches:
            raise ValueError(
                "Invalid piano roll pitch dimension. "
                f"Expected {expected_pitches}, "
                f"got {piano_roll.shape[1]}."
            )
