import logging
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class NoteEvent:
    """Represent a detected musical note event.

    Attributes:
        pitch:
            MIDI pitch number.
        start_time:
            Note onset time in seconds.
        end_time:
            Note offset time in seconds.
        velocity:
            MIDI velocity value.
    """

    pitch: int
    start_time: float
    end_time: float
    velocity: int = 100

    @property
    def duration(self) -> float:
        """Return note duration in seconds.

        Returns:
            Duration between onset and offset.
        """
        return self.end_time - self.start_time


class NoteTracker:
    """Convert binary piano-roll predictions into musical notes.

    The input piano roll is expected to have the shape:

        ``(n_frames, n_pitches)``

    Consecutive active frames are merged into a single note event.

    Attributes:
        hop_length:
            Number of audio samples between consecutive frames.
        sample_rate:
            Audio sampling rate.
        midi_pitch_min:
            Lowest MIDI pitch represented by the piano roll.
        midi_pitch_max:
            Highest MIDI pitch represented by the piano roll.
        min_note_duration:
            Minimum duration required to keep a detected note.
        velocity:
            MIDI velocity assigned to generated notes.
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
        """Initialize the note tracker.

        Args:
            hop_length:
                STFT hop length used during feature extraction.
            sample_rate:
                Audio sampling rate.
            midi_pitch_min:
                Lowest supported MIDI pitch.
            midi_pitch_max:
                Highest supported MIDI pitch.
            min_note_duration:
                Minimum note duration in seconds.
            velocity:
                MIDI velocity.

        Raises:
            ValueError:
                If parameters are invalid.
        """

        if hop_length <= 0:
            raise ValueError("hop_length must be strictly positive.")

        if sample_rate <= 0:
            raise ValueError("sample_rate must be strictly positive.")

        if midi_pitch_min > midi_pitch_max:
            raise ValueError("midi_pitch_min must be lower than midi_pitch_max.")

        if min_note_duration < 0:
            raise ValueError("min_note_duration cannot be negative.")

        if not 0 <= velocity <= 127:
            raise ValueError("velocity must be between 0 and 127.")

        self._hop_length = hop_length
        self._sample_rate = sample_rate
        self._midi_pitch_min = midi_pitch_min
        self._midi_pitch_max = midi_pitch_max
        self._min_note_duration = min_note_duration
        self._velocity = velocity

        self._frame_duration = hop_length / sample_rate

    def extract_notes(
        self,
        piano_roll: NDArray[np.bool_],
    ) -> list[NoteEvent]:
        """Extract note events from a binary piano roll.

        Args:
            piano_roll:
                Binary piano roll with shape:

                ``(n_frames, n_pitches)``

        Returns:
            List of reconstructed musical notes.

        Raises:
            ValueError:
                If the piano roll shape is invalid.
        """

        self._validate_piano_roll(piano_roll)

        n_frames, n_pitches = piano_roll.shape

        logger.info(
            "Starting note tracking: frames=%d, pitches=%d.",
            n_frames,
            n_pitches,
        )

        notes: list[NoteEvent] = []

        for pitch_index in range(n_pitches):
            pitch = self._midi_pitch_min + pitch_index

            notes.extend(
                self._extract_pitch_notes(
                    piano_roll[:, pitch_index],
                    pitch,
                )
            )

        logger.info(
            "Note tracking completed: detected_notes=%d.",
            len(notes),
        )

        return notes

    def _extract_pitch_notes(
        self,
        activations: NDArray[np.bool_],
        pitch: int,
    ) -> list[NoteEvent]:
        """Extract notes for a single MIDI pitch.

        Args:
            activations:
                Binary activation sequence.
            pitch:
                MIDI pitch number.

        Returns:
            List of detected notes.
        """

        notes: list[NoteEvent] = []

        start_frame: int | None = None

        for frame_index, active in enumerate(activations):
            if active and start_frame is None:
                start_frame = frame_index

            elif not active and start_frame is not None:
                notes.append(
                    self._create_note(
                        pitch,
                        start_frame,
                        frame_index,
                    )
                )

                start_frame = None

        if start_frame is not None:
            notes.append(
                self._create_note(
                    pitch,
                    start_frame,
                    len(activations),
                )
            )

        filtered_notes = [
            note for note in notes if note.duration >= self._min_note_duration
        ]

        removed = len(notes) - len(filtered_notes)

        if removed:
            logger.debug(
                "Filtered %d short notes for pitch=%d.",
                removed,
                pitch,
            )

        return filtered_notes

    def _create_note(
        self,
        pitch: int,
        start_frame: int,
        end_frame: int,
    ) -> NoteEvent:
        """Create a note event from frame boundaries.

        Args:
            pitch:
                MIDI pitch.
            start_frame:
                Starting frame index.
            end_frame:
                Ending frame index.

        Returns:
            Musical note event.
        """

        return NoteEvent(
            pitch=pitch,
            start_time=start_frame * self._frame_duration,
            end_time=end_frame * self._frame_duration,
            velocity=self._velocity,
        )

    def _validate_piano_roll(
        self,
        piano_roll: NDArray[np.bool_],
    ) -> None:
        """Validate piano-roll dimensions.

        Args:
            piano_roll:
                Binary piano-roll tensor.

        Raises:
            ValueError:
                If dimensions are invalid.
        """

        if piano_roll.ndim != 2:
            raise ValueError(
                (
                    "Piano roll must have shape "
                    f"(frames, pitches), got {piano_roll.shape}."
                )
            )

        expected_pitches = self._midi_pitch_max - self._midi_pitch_min + 1

        actual_pitches = piano_roll.shape[1]

        if actual_pitches != expected_pitches:
            raise ValueError(
                ("Invalid piano roll pitch dimension: expected=%d, received=%d."),
            )

    @property
    def frame_duration(self) -> float:
        """Return duration of one prediction frame.

        Returns:
            Frame duration in seconds.
        """
        return self._frame_duration
