import logging
from dataclasses import dataclass

import numpy as np
from core.processing_settings import ProcessingSettings
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DetectedNote:
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
        settings:
            Global processing configuration.
        min_note_duration:
            Minimum note duration in seconds.
        velocity:
            Default MIDI velocity.
    """

    def __init__(
        self,
        settings: ProcessingSettings,
    ) -> None:

        self.settings = settings
        self.frame_duration = settings.hop_length / settings.target_sample_rate

    def extract_notes(
        self,
        piano_roll: NDArray[np.bool_],
    ) -> list[DetectedNote]:
        """Extract note events from a binary piano roll.

        Args:
            piano_roll:
                Binary matrix with shape:

                    (n_frames, n_pitches)

        Returns:
            List of detected notes.
        """

        self._validate_piano_roll(piano_roll)

        notes: list[DetectedNote] = []

        n_frames, n_pitches = piano_roll.shape

        logger.info(
            f"Tracking notes from piano roll ({n_frames} frames, {n_pitches} pitches)."
        )

        for pitch_idx in range(n_pitches):
            pitch = self.settings.midi_pitch_min + pitch_idx

            activations = piano_roll[:, pitch_idx]

            notes.extend(self._extract_pitch_notes(activations, pitch))

        logger.info(f"Detected {len(notes)} notes.")

        return notes

    def _extract_pitch_notes(
        self,
        activations: NDArray[np.bool_],
        pitch: int,
    ) -> list[DetectedNote]:
        """Extract consecutive activations for one pitch."""

        notes: list[DetectedNote] = []

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

        return [
            note for note in notes if note.duration >= self.settings.min_note_duration
        ]

    def _create_note(
        self,
        pitch: int,
        start_frame: int,
        end_frame: int,
    ) -> DetectedNote:
        """Create note from frame boundaries."""

        return DetectedNote(
            pitch=pitch,
            start_time=(start_frame * self.frame_duration),
            end_time=(end_frame * self.frame_duration),
            velocity=self.settings.velocity,
        )

    def _validate_piano_roll(
        self,
        piano_roll: NDArray[np.bool_],
    ) -> None:
        """Validate piano roll dimensions."""

        if piano_roll.ndim != 2:
            raise ValueError("Piano roll must have shape (frames, pitches).")

        expected_pitches = (
            self.settings.midi_pitch_max - self.settings.midi_pitch_min + 1
        )

        if piano_roll.shape[1] != expected_pitches:
            raise ValueError(
                "Invalid piano roll pitch dimension. "
                f"Expected {expected_pitches}, "
                f"got {piano_roll.shape[1]}."
            )
