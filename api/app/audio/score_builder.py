import logging
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
        output_dir: str | Path = "output",
        bpm: int = 120,
        lilypond_binary: str = "lilypond",
    ) -> None:
        """
        Initialize score builder.

        Args:
            output_dir:
                Directory where generated files are stored.

            bpm:
                Tempo of the generated score.

            lilypond_binary:
                LilyPond executable name or path.
        """

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.bpm = bpm
        self.lilypond_binary = lilypond_binary

    def build_musicxml(
        self,
        notes: list[QuantizedNoteEvent],
        filename: str = "transcription.musicxml",
    ) -> Path:
        """
        Build a MusicXML score from quantized notes.

        Args:
            notes:
                Quantized musical events.

            filename:
                Output MusicXML filename.

        Returns:
            Path of generated MusicXML file.
        """

        logger.info(f"Building MusicXML from {len(notes)} notes.")

        score = stream.Score()

        part = stream.Part()

        part.insert(
            0,
            tempo.MetronomeMark(number=self.bpm),
        )

        for event in notes:
            current_note = note.Note(event.pitch)

            current_note.duration.quarterLength = event.duration

            part.insert(event.offset, current_note)

        score.append(part)

        output_path = self.output_dir / filename

        score.write("musicxml", fp=output_path)

        logger.info(f"MusicXML generated: {output_path}")

        return output_path

    def build_lilypond(
        self,
        musicxml_path: Path,
        filename: str = "transcription.ly",
    ) -> Path:
        """
        Convert MusicXML into a LilyPond source file.

        Args:
            musicxml_path:
                Input MusicXML file.

            filename:
                Output LilyPond filename.

        Returns:
            Path of generated LilyPond file.
        """

        output_path = self.output_dir / filename

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

        logger.info("Rendering score with LilyPond.")

        self._run_lilypond(musicxml_path, output_format="pdf")

        self._run_lilypond(musicxml_path, output_format="svg")

        pdf_path = self.output_dir / f"{musicxml_path.stem}.pdf"

        svg_path = self.output_dir / f"{musicxml_path.stem}.svg"

        return pdf_path, svg_path

    def _run_lilypond(
        self,
        input_file: Path,
        output_format: str,
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

        if output_format not in {"pdf", "svg"}:
            raise ValueError(f"Unsupported LilyPond format: {output_format}")

        command = [
            self.lilypond_binary,
            f"--{output_format}",
            "--output",
            str(self.output_dir),
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
