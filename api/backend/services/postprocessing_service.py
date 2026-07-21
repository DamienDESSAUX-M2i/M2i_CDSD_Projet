import logging
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np
import pretty_midi
from numpy.typing import NDArray

from backend.audio import (
    BeatTracker,
    MidiBuilder,
    NoteEvent,
    NoteTracker,
    PianoRollRenderer,
    QuantizedNoteEvent,
    RhythmQuantizer,
    ScoreBuilder,
)
from backend.core import ProcessingSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PostprocessingResult:
    """Artifacts generated after model inference.

    Attributes:
        postprocessing_time:
            Total post-processing duration in seconds.

        notes:
            Raw musical notes extracted from the piano roll.

        quantized_notes:
            Rhythmically quantized musical notes.

        midi:
            Generated MIDI object.

        tempo:
            Estimated tempo in beats per minute.

        musicxml_path:
            Path to generated MusicXML file.

        midi_path:
            Path to generated MIDI file.

        piano_roll_png_path:
            Path to rendered piano roll PNG image.

        piano_roll_svg_path:
            Path to rendered piano roll SVG image.

        score_pdf_path:
            Path to rendered score PDF if available.

        score_svg_path:
            Path to rendered score SVG if available.
    """

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
    """Generate musical artifacts from model predictions.

    This service converts frame-level neural network predictions into
    human-readable musical formats:

        1. Piano roll to note events.
        2. MIDI generation.
        3. Piano roll rendering.
        4. Beat tracking.
        5. Rhythm quantization.
        6. MusicXML generation.
        7. Score rendering.
    """

    def __init__(
        self,
        settings: ProcessingSettings,
    ) -> None:
        """Initialize the post-processing pipeline.

        Args:
            settings:
                Processing configuration.
        """
        self._settings: ProcessingSettings = settings

        self._note_tracker: NoteTracker = NoteTracker(
            hop_length=settings.hop_length,
            sample_rate=settings.target_sample_rate,
            midi_pitch_min=settings.midi_pitch_min,
            midi_pitch_max=settings.midi_pitch_max,
            min_note_duration=settings.min_piano_roll_note_duration,
            velocity=settings.velocity,
        )

        self._beat_tracker: BeatTracker = BeatTracker(
            hop_length=settings.hop_length,
        )

        self._quantizer: RhythmQuantizer = RhythmQuantizer(
            subdivision=settings.subdivision,
            min_note_duration=(settings.min_rhythm_quantizer_note_duration),
        )

        self._midi_builder: MidiBuilder = MidiBuilder(
            velocity=settings.velocity,
        )

        self._piano_roll_renderer: PianoRollRenderer = PianoRollRenderer(
            pitch_min=settings.midi_pitch_min,
            pitch_max=settings.midi_pitch_max,
        )

        self._score_builder: ScoreBuilder = ScoreBuilder()

    def process(
        self,
        processing_id: str,
        piano_roll: NDArray[np.bool_],
        audio: NDArray[np.float32],
        sample_rate: int,
    ) -> PostprocessingResult:
        """Execute the complete post-processing pipeline.

        Args:
            processing_id:
                Unique identifier of the transcription process.

            piano_roll:
                Binary piano-roll predicted by the neural network.

            audio:
                Preprocessed mono waveform.

            sample_rate:
                Audio sampling rate.

        Returns:
            Generated musical artifacts.

        Raises:
            Exception:
                If one of the post-processing stages fails.
        """
        logger.info(
            "Starting post-processing (processing_id=%s).",
            processing_id,
        )

        start_time = perf_counter()

        output_dir = self._settings.output_dir / processing_id
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            note_start = perf_counter()

            notes = self._note_tracker.extract_notes(piano_roll)

            logger.debug(
                "Note extraction completed in %.3f s (%d notes).",
                perf_counter() - note_start,
                len(notes),
            )

            midi_start = perf_counter()

            midi = self._midi_builder.build(notes)

            midi_path = output_dir / "transcription.mid"

            self._midi_builder.save(midi=midi, output_path=midi_path)

            logger.debug(
                "MIDI generation completed in %.3f s.",
                perf_counter() - midi_start,
            )

            piano_roll_start = perf_counter()

            piano_roll_png_path = output_dir / "piano_roll.png"
            piano_roll_svg_path = output_dir / "piano_roll.svg"

            self._piano_roll_renderer.render(
                notes=notes, png_path=piano_roll_png_path, svg_path=piano_roll_svg_path
            )

            logger.debug(
                "Piano roll rendering completed in %.3f s.",
                perf_counter() - piano_roll_start,
            )

            beat_start = perf_counter()

            beat_result = self._beat_tracker.track(audio=audio, sample_rate=sample_rate)

            logger.debug(
                "Beat tracking completed in %.3f s.",
                perf_counter() - beat_start,
            )

            logger.info(
                "Estimated tempo: %.0f BPM.",
                beat_result.tempo,
            )

            quantization_start = perf_counter()

            quantized_notes = self._quantizer.quantize(
                notes=notes, beat_times=beat_result.beat_times
            )

            logger.debug(
                "Rhythm quantization completed in %.3f s.",
                perf_counter() - quantization_start,
            )

            musicxml_path = output_dir / "transcription.musicxml"

            score_start = perf_counter()

            self._score_builder.build_musicxml(
                notes=quantized_notes, output_path=musicxml_path, bpm=beat_result.tempo
            )

            score_pdf_path, score_svg_path = self._score_builder.render(
                musicxml_path=musicxml_path
            )

            logger.debug(
                "Score generation completed in %.3f s.",
                perf_counter() - score_start,
            )

        except Exception:
            logger.exception(
                "Post-processing failed (processing_id=%s).",
                processing_id,
            )
            raise

        postprocessing_time = perf_counter() - start_time

        logger.info(
            ("Post-processing completed in %.3f s (processing_id=%s)."),
            postprocessing_time,
            processing_id,
        )

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
