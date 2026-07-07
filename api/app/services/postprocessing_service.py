import logging
from dataclasses import dataclass

import numpy as np
import pretty_midi
from core import PROCESSING_SETTINGS
from numpy.typing import NDArray

from .midi_builder import MidiBuilder
from .note_tracker import NoteTracker
from .piano_roll_renderer import PianoRollRenderer
from .score_builder import ScoreBuilder


@dataclass(slots=True)
class PostprocessingResult:
    """Artifacts produced after model inference."""

    piano_roll: NDArray[np.bool_]
    midi: pretty_midi.PrettyMIDI
    note_count: int
    duration_seconds: float


logger = logging.getLogger(__name__)


class PostprocessingService:
    """Convert model predictions into musical artifacts."""

    def __init__(
        self,
    ) -> None:
        self._tracker = NoteTracker(PROCESSING_SETTINGS)
        self._midi_builder = MidiBuilder(velocity=PROCESSING_SETTINGS.velocity)
        self.piano_roll_randerer = PianoRollRenderer(
            pitch_min=PROCESSING_SETTINGS.midi_pitch_min,
            pitch_max=PROCESSING_SETTINGS.midi_pitch_max,
            output_dir=PROCESSING_SETTINGS.output_dir,
        )
        self._score_builder = ScoreBuilder(
            output_dir=PROCESSING_SETTINGS.output_dir, bpm=120
        )

    def process(
        self,
        piano_roll,
    ):
        """Generate all post-processing artifacts."""

        logger.info("Starting post-processing.")

        notes = self._tracker.extract_notes(piano_roll)

        midi = self._midi_builder.build(notes)

        self._midi_builder.save(midi, PROCESSING_SETTINGS.output_dir / "result.mid")

        piano_roll_bytes, piano_roll_svg_path = self.piano_roll_randerer.render(notes)

        musicxml_path = self._score_builder.build_musicxml(notes)

        score_pdf_path, score_svg_path = self._score_builder.export_rendered_score(
            musicxml_path
        )

        logger.info(f"Extracted {len(notes)} notes.")

        return midi
