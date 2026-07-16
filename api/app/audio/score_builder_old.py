import logging
import shutil
import subprocess
from pathlib import Path

from music21 import note, stream, tempo

from .rhythm_quantizer import QuantizedNoteEvent

logger = logging.getLogger(__name__)


class ScoreBuilder:
    """
    Build and export musical scores from quantized MIDI events.

    Workflow:

        QuantizedNoteEvent[]
                |
                v
            music21
                |
                v
           MusicXML
                |
                v
           LilyPond
                |
          +-----+------+
          |            |
          v            v
         PDF          SVG


    Notes:
        Rhythm quantization is performed upstream by RhythmQuantizer.
        This class only converts symbolic musical events into notation
        formats and renders the final score.
    """

    def __init__(
        self,
        lilypond_binary: str = "lilypond",
    ) -> None:
        """
        Initialize score builder.

        Args:
            lilypond_binary:
                LilyPond executable name or path.
        """

        self.lilypond_binary = lilypond_binary
        self._lilypond_available = shutil.which(lilypond_binary) is not None

    @property
    def has_lilypond(self) -> bool:
        """Return whether the LilyPond executable is available."""

        return self._lilypond_available

    def build_musicxml(
        self,
        notes: list[QuantizedNoteEvent],
        output_path: Path,
        bpm: int = 120,
    ) -> None:
        """
        Build a MusicXML score from quantized notes.

        Args:
            notes:
                Quantized musical events.

            output_path:
                MusicXML output path.

            bpm:
                Tempo of the generated score.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Building MusicXML from {len(notes)} notes.")

        score = stream.Score()

        part = stream.Part()

        part.insert(
            0,
            tempo.MetronomeMark(number=bpm),
        )

        for event in notes:
            current_note = note.Note(event.pitch)

            current_note.duration.quarterLength = event.duration

            part.insert(event.offset, current_note)

        score.append(part)

        score.write("musicxml", fp=output_path)

        logger.info(f"MusicXML generated: {output_path}")

        return output_path

    def build_lilypond(
        self,
        musicxml_path: Path,
        output_path: Path,
    ) -> None:
        """
        Convert MusicXML into a LilyPond source file.

        Args:
            musicxml_path:
                Input MusicXML file.

            output_path:
                Output LilyPond output path.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)

        command = [
            self.lilypond_binary,
            "--pdf",
            "--output",
            str(self.output_dir),
            str(musicxml_path),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "LilyPond conversion failed.\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

        return output_path

    def export_rendered_score(
        self,
        musicxml_path: Path,
    ) -> tuple[Path, Path]:
        """
        Render a MusicXML score into PDF and SVG.

        Args:
            musicxml_path:
                Source MusicXML file.

        Returns:
            Tuple containing:
                - PDF output path
                - SVG output path
        """

        musicxml_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.has_lilypond:
            logger.warning(
                f"LilyPond executable '{self.lilypond_binary}' not found. "
                f"Skipping score rendering."
            )
            return None, None

        logger.info("Rendering score with LilyPond.")

        self._run_lilypond(
            input_file=musicxml_path,
            output_format="pdf",
            output_dir=musicxml_path.parent,
        )

        self._run_lilypond(
            input_file=musicxml_path,
            output_format="svg",
            output_dir=musicxml_path.parent,
        )

        pdf_path = musicxml_path.parent / f"{musicxml_path.stem}.pdf"

        svg_path = musicxml_path.parent / f"{musicxml_path.stem}.svg"

        return pdf_path, svg_path

    def _run_lilypond(
        self, input_file: Path, output_format: str, output_dir: Path
    ) -> None:
        """
        Execute LilyPond rendering.

        Args:
            input_file:
                Input MusicXML file.

            output_format:
                Rendering format:
                    - pdf
                    - svg

        Raises:
            ValueError:
                If format is unsupported.

            RuntimeError:
                If LilyPond execution fails.
        """

        output_dir.mkdir(parents=True, exist_ok=True)

        if output_format not in {"pdf", "svg"}:
            raise ValueError(f"Unsupported LilyPond format: {output_format}")

        command = [
            self.lilypond_binary,
            f"--{output_format}",
            "--output",
            str(output_dir),
            str(input_file),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "LilyPond rendering failed.\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
