import logging
from pathlib import Path

import pretty_midi

from .note_tracker import NoteEvent

logger = logging.getLogger(__name__)


class MidiBuilder:
    """Build MIDI files from detected musical notes.

    This class converts a list of :class:`DetectedNote`
    into a PrettyMIDI object.

    Responsibilities:
        - Create MIDI instruments.
        - Convert detected notes into MIDI notes.
        - Validate note parameters.
        - Export MIDI files.

    It does not perform:
        - note detection;
        - thresholding;
        - piano-roll processing.
    """

    def __init__(self, velocity: int = 100, instrument_program: int = 0) -> None:
        """Initialize MIDI builder.

        Args:
            instrument_program:
                General MIDI instrument program number.
                Default value 0 corresponds to acoustic piano.

            velocity:
                Default MIDI velocity.
        """

        self.velocity = velocity
        self.instrument_program = instrument_program

    def build(self, notes: list[NoteEvent]) -> pretty_midi.PrettyMIDI:
        """Create a PrettyMIDI object.

        Args:
            notes:
                List of detected musical notes.

        Returns:
            A PrettyMIDI object.
        """

        logger.info(f"Building MIDI from {len(notes)} notes.")

        midi = pretty_midi.PrettyMIDI()

        instrument = pretty_midi.Instrument(program=self.instrument_program)

        for note in notes:
            midi_note = self._convert_note(note)

            instrument.notes.append(midi_note)

        midi.instruments.append(instrument)

        return midi

    def save(self, midi: pretty_midi.PrettyMIDI, output_path: Path) -> None:
        """Save MIDI object to disk.

        Args:
            midi:
                PrettyMIDI object.

            output_path:
                Destination MIDI file.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)

        midi.write(str(output_path))

        logger.info(f"MIDI saved: {output_path}")

    def _convert_note(
        self,
        note: NoteEvent,
    ) -> pretty_midi.Note:
        """Convert detected note into PrettyMIDI note."""

        self._validate_note(note)

        return pretty_midi.Note(
            velocity=(note.velocity if note.velocity is not None else self.velocity),
            pitch=note.pitch,
            start=note.start_time,
            end=note.end_time,
        )

    def _validate_note(
        self,
        note: NoteEvent,
    ) -> None:
        """Validate MIDI note parameters."""

        if not 0 <= note.pitch <= 127:
            raise ValueError(f"Invalid MIDI pitch: {note.pitch}")

        if note.start_time < 0:
            raise ValueError("Note start time cannot be negative.")

        if note.end_time <= note.start_time:
            raise ValueError("Note duration must be positive.")

        if not 0 <= note.velocity <= 127:
            raise ValueError(f"Invalid MIDI velocity: {note.velocity}")
