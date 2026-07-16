import logging
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import pretty_midi
from numpy.typing import NDArray

from app.audio import (
    BeatTracker,
    MidiBuilder,
    NoteEvent,
    NoteTracker,
    PianoRollRenderer,
    QuantizedNoteEvent,
    RhythmQuantizer,
    ScoreBuilder,
)
from app.core import ProcessingSettings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PostprocessingResult:
    """Artifacts generated after model inference."""

    postprocessing_time: float
    notes: list[NoteEvent]
    quantized_notes: list[QuantizedNoteEvent]
    midi: pretty_midi.PrettyMIDI
    tempo: float
    musicxml_path: Path
    midi_path: Path
    piano_roll_png_path: Path
    piano_roll_svg_path: Path
    score_pdf_path: Path | None
    score_svg_path: Path | None


class PostprocessingService:
    """Convert frame-wise predictions into musical artifacts."""

    def __init__(self, settings: ProcessingSettings) -> None:

        self.settings = settings

        self.output_dir = self.settings.output_dir

        self._note_tracker = NoteTracker(
            hop_length=self.settings.hop_length,
            sample_rate=self.settings.target_sample_rate,
            midi_pitch_min=self.settings.midi_pitch_min,
            midi_pitch_max=self.settings.midi_pitch_max,
            min_note_duration=self.settings.min_piano_roll_note_duration,
            velocity=self.settings.velocity,
        )

        self._beat_tracker = BeatTracker(
            hop_length=settings.hop_length,
        )

        self._quantizer = RhythmQuantizer(
            subdivision=self.settings.subdivision,
            min_note_duration=self.settings.min_rhytm_quantizer_note_duration,
        )

        self._midi_builder = MidiBuilder(velocity=self.settings.velocity)

        self._piano_roll_renderer = PianoRollRenderer(
            pitch_min=self.settings.midi_pitch_min,
            pitch_max=self.settings.midi_pitch_max,
        )

        self._score_builder = ScoreBuilder()

    def process(
        self,
        processing_id: str,
        piano_roll: NDArray,
        audio: NDArray,
        sample_rate: int,
    ) -> PostprocessingResult:
        """
        Execute the complete post-processing pipeline.

        Args:
            piano_roll:
                Binary piano-roll predicted by the neural network.

            audio:
                Preprocessed mono waveform.

            sample_rate:
                Audio sampling rate.

        Returns:
            All generated musical artifacts.
        """

        logger.info("Starting post-processing.")

        t0 = perf_counter()

        # ===
        # Frame -> notes
        # ===

        notes = self._note_tracker.extract_notes(piano_roll)

        logger.info("%d notes extracted.", len(notes))

        # ===
        # MIDI
        # ===

        midi = self._midi_builder.build(notes)

        midi_path = self.settings.output_dir / processing_id / "transcription.mid"

        self._midi_builder.save(
            midi=midi,
            output_path=midi_path,
        )

        # ===
        # Piano roll
        # ===

        piano_roll_png_path = (
            self.settings.output_dir / processing_id / "piano_roll.png"
        )

        piano_roll_svg_path = (
            self.settings.output_dir / processing_id / "piano_roll.svg"
        )

        self._piano_roll_renderer.render(
            notes=notes,
            png_path=piano_roll_png_path,
            svg_path=piano_roll_svg_path,
        )

        # ===
        # Beat tracking
        # ===

        beat_result = self._beat_tracker.track(audio=audio, sample_rate=sample_rate)

        logger.info(f"Estimated tempo: {beat_result.tempo:.0f} BPM.")

        # ===
        # Rhythm quantization
        # ===

        quantized_notes = self._quantizer.quantize(
            notes=notes,
            beat_times=beat_result.beat_times,
        )

        # ===
        # MusicXML
        # ===

        musicxml_path = (
            self.settings.output_dir / processing_id / "transcription.musicxlm"
        )

        self._score_builder.build_musicxml(
            notes=quantized_notes,
            output_path=musicxml_path,
            bpm=beat_result.tempo,
        )

        # ===
        # Score rendering
        # ===

        score_pdf_path, score_svg_path = self._score_builder.render(
            musicxml_path=musicxml_path
        )

        postprocessing_time = perf_counter() - t0

        logger.info(f"Post-processing completed in {postprocessing_time:.3f} s.")

        return PostprocessingResult(
            postprocessing_time=postprocessing_time,
            notes=notes,
            quantized_notes=quantized_notes,
            midi=midi,
            tempo=beat_result.tempo,
            musicxml_path=musicxml_path,
            midi_path=midi_path,
            piano_roll_png_path=piano_roll_png_path,
            piano_roll_svg_path=piano_roll_svg_path,
            score_pdf_path=score_pdf_path,
            score_svg_path=score_svg_path,
        )
