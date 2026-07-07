from __future__ import annotations

import subprocess
from pathlib import Path

from domain.note_event import NoteEvent
from music21 import note, stream, tempo


class ScoreBuilder:
    """
    Build and export musical scores from detected MIDI events.

    The workflow is:

        NoteEvent[]
            |
            v
        MusicXML
            |
            v
        MuseScore
            |
            +--> PDF
            |
            +--> SVG

    Attributes:
        output_dir:
            Directory where generated files are stored.
        bpm:
            Score tempo.
    """

    def __init__(
        self,
        output_dir: str | Path = "output",
        bpm: int = 120,
        musescore_binary: str = "musescore",
    ) -> None:
        """
        Initialize score builder.

        Args:
            output_dir:
                Directory used for generated files.
            bpm:
                Default tempo of generated score.
            musescore_binary:
                MuseScore executable name.
        """

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.bpm = bpm
        self.musescore_binary = musescore_binary

    def build_musicxml(
        self,
        notes: list[NoteEvent],
        filename: str = "transcription.musicxml",
    ) -> Path:
        """
        Create a MusicXML file from detected notes.

        Args:
            notes:
                Detected MIDI note events.
            filename:
                Output MusicXML filename.

        Returns:
            Path of generated MusicXML file.
        """

        score = stream.Score()

        part = stream.Part()

        part.insert(
            0,
            tempo.MetronomeMark(
                number=self.bpm,
            ),
        )

        for event in notes:
            duration_seconds = event.end_time - event.start_time

            quarter_length = duration_seconds * self.bpm / 60

            current_note = note.Note(
                event.pitch,
            )

            current_note.duration.quarterLength = quarter_length

            part.append(current_note)

        score.append(part)

        output_path = self.output_dir / filename

        score.write(
            "musicxml",
            fp=output_path,
        )

        return output_path

    def export_rendered_score(
        self,
        musicxml_path: Path,
        pdf_filename: str = "transcription.pdf",
        svg_filename: str = "transcription.svg",
    ) -> tuple[Path, Path]:
        """
        Render MusicXML into PDF and SVG using MuseScore.

        Args:
            musicxml_path:
                Existing MusicXML file.
            pdf_filename:
                Generated PDF filename.
            svg_filename:
                Generated SVG filename.

        Returns:
            Tuple containing:
                - PDF output path
                - SVG output path

        Raises:
            RuntimeError:
                If MuseScore rendering fails.
        """

        pdf_path = self.output_dir / pdf_filename

        svg_path = self.output_dir / svg_filename

        self._export_with_musescore(
            input_file=musicxml_path,
            output_file=pdf_path,
        )

        self._export_with_musescore(
            input_file=musicxml_path,
            output_file=svg_path,
        )

        return pdf_path, svg_path

    def _export_with_musescore(
        self,
        input_file: Path,
        output_file: Path,
    ) -> None:
        """
        Export a MusicXML file using MuseScore CLI.

        Args:
            input_file:
                Source MusicXML file.
            output_file:
                Destination rendered file.

        Raises:
            RuntimeError:
                If MuseScore returns an error.
        """

        command = [
            self.musescore_binary,
            str(input_file),
            "-o",
            str(output_file),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "MuseScore export failed.\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
