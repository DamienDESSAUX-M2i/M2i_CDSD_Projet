import logging
from pathlib import Path

import pretty_midi

from .note_tracker import NoteEvent

logger = logging.getLogger(__name__)


class MidiBuilder:
    """Build MIDI files from detected musical note events.

    This class converts reconstructed note events into a valid MIDI file
    using the PrettyMIDI library.

    Responsibilities:
        - Create MIDI instruments.
        - Convert note events into MIDI notes.
        - Validate MIDI constraints.
        - Persist MIDI files.

    This class does not perform:
        - note detection;
        - thresholding;
        - piano-roll decoding.
    """

    def __init__(
        self,
        velocity: int = 100,
        instrument_program: int = 0,
    ) -> None:
        """Initialize the MIDI builder.

        Args:
            velocity:
                Default MIDI velocity used when a note does not provide one.
            instrument_program:
                General MIDI program number.
                Value ``0`` corresponds to acoustic grand piano.

        Raises:
            ValueError:
                If velocity or instrument program are outside MIDI ranges.
        """

        if not 0 <= velocity <= 127:
            raise ValueError("velocity must be between 0 and 127.")

        if not 0 <= instrument_program <= 127:
            raise ValueError("instrument_program must be between 0 and 127.")

        self._velocity = velocity
        self._instrument_program = instrument_program

    def build(
        self,
        notes: list[NoteEvent],
    ) -> pretty_midi.PrettyMIDI:
        """Build a MIDI object from detected notes.

        Args:
            notes:
                List of musical note events.

        Returns:
            PrettyMIDI object containing one instrument track.

        Raises:
            ValueError:
                If note validation fails.
        """

        logger.info(
            "Building MIDI file: notes=%d.",
            len(notes),
        )

        if not notes:
            logger.warning("Building empty MIDI sequence.")

        midi = pretty_midi.PrettyMIDI()

        instrument = pretty_midi.Instrument(program=self._instrument_program)

        for note_event in notes:
            instrument.notes.append(self._convert_note(note_event))

        midi.instruments.append(instrument)

        logger.debug(
            "MIDI object created: instruments=%d, notes=%d.",
            len(midi.instruments),
            len(instrument.notes),
        )

        return midi

    def save(
        self,
        midi: pretty_midi.PrettyMIDI,
        output_path: Path,
    ) -> None:
        """Save a MIDI object to disk.

        Args:
            midi:
                PrettyMIDI object to serialize.

            output_path:
                Destination file path.

        Raises:
            ValueError:
                If the output file extension is invalid.
        """

        if output_path.suffix.lower() not in {".mid", ".midi"}:
            raise ValueError("MIDI output path must have a .mid or .midi extension.")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Saving MIDI file: path=%s.",
            output_path,
        )

        midi.write(str(output_path))

        logger.info("MIDI file saved successfully.")

    def _convert_note(
        self,
        note: NoteEvent,
    ) -> pretty_midi.Note:
        """Convert internal note representation into PrettyMIDI format.

        Args:
            note:
                Internal detected note event.

        Returns:
            PrettyMIDI note object.
        """

        self._validate_note(note)

        return pretty_midi.Note(
            velocity=(note.velocity if note.velocity is not None else self._velocity),
            pitch=note.pitch,
            start=note.start_time,
            end=note.end_time,
        )

    def _validate_note(
        self,
        note: NoteEvent,
    ) -> None:
        """Validate MIDI note constraints.

        Args:
            note:
                Note event to validate.

        Raises:
            ValueError:
                If note parameters are invalid.
        """

        if not 0 <= note.pitch <= 127:
            raise ValueError(f"Invalid MIDI pitch: {note.pitch}.")

        if note.start_time < 0:
            raise ValueError("Note start time cannot be negative.")

        if note.end_time <= note.start_time:
            raise ValueError("Note end time must be greater than start time.")

        if not 0 <= note.velocity <= 127:
            raise ValueError(f"Invalid MIDI velocity: {note.velocity}.")
