import io
from pathlib import Path

import matplotlib.pyplot as plt

from .note_tracker import DetectedNote


class PianoRollRenderer:
    """
    Render MIDI note events as piano roll images.

    Supported outputs:
        - PNG image
        - SVG vector image
        - raw PNG bytes for HTTP responses
    """

    def __init__(
        self,
        pitch_min: int = 40,
        pitch_max: int = 88,
        output_dir: str | Path = "output",
        figsize: tuple[int, int] = (12, 5),
    ) -> None:
        """
        Initialize piano roll renderer.

        Args:
            pitch_min:
                Lowest MIDI pitch displayed.
            pitch_max:
                Highest MIDI pitch displayed.
            output_dir:
                Directory where generated files are saved.
            figsize:
                Matplotlib figure size.
        """

        self.pitch_min = pitch_min
        self.pitch_max = pitch_max
        self.output_dir = Path(output_dir)
        self.figsize = figsize

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _create_figure(
        self,
        notes: list[DetectedNote],
    ):
        """
        Create matplotlib piano roll figure.

        Args:
            notes:
                Detected MIDI notes.

        Returns:
            Matplotlib figure and axis.
        """

        fig, ax = plt.subplots(
            figsize=self.figsize,
        )

        for note in notes:
            duration = note.end_time - note.start_time

            ax.barh(
                y=note.pitch,
                width=duration,
                left=note.start_time,
                height=0.8,
            )

        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("MIDI pitch")

        ax.set_ylim(
            self.pitch_min - 1,
            self.pitch_max + 1,
        )

        ax.set_title("Guitar transcription piano roll")

        ax.grid(True)

        return fig, ax

    def render_png(
        self,
        notes: list[DetectedNote],
        filename: str = "piano_roll.png",
    ) -> bytes:
        """
        Render piano roll as PNG.

        The image is also saved locally.

        Args:
            notes:
                Detected MIDI notes.
            filename:
                Output filename.

        Returns:
            PNG encoded image bytes.
        """

        fig, _ = self._create_figure(notes)

        buffer = io.BytesIO()

        fig.tight_layout()

        fig.savefig(
            buffer,
            format="png",
            dpi=150,
            bbox_inches="tight",
        )

        fig.savefig(
            self.output_dir / filename,
            format="png",
            dpi=150,
            bbox_inches="tight",
        )

        plt.close(fig)

        buffer.seek(0)

        return buffer.getvalue()

    def render_svg(
        self,
        notes: list[DetectedNote],
        filename: str = "piano_roll.svg",
    ) -> Path:
        """
        Render piano roll as SVG.

        Args:
            notes:
                Detected MIDI notes.
            filename:
                Output filename.

        Returns:
            Path to generated SVG file.
        """

        fig, _ = self._create_figure(notes)

        fig.tight_layout()

        output_path = self.output_dir / filename

        fig.savefig(
            output_path,
            format="svg",
            bbox_inches="tight",
        )

        plt.close(fig)

        return output_path

    def render(
        self,
        notes: list[DetectedNote],
    ) -> tuple[bytes, Path]:
        """
        Render both PNG and SVG outputs.

        Args:
            notes:
                Detected MIDI notes.

        Returns:
            Tuple containing:
                - PNG image bytes
                - SVG file path
        """

        png_bytes = self.render_png(notes)

        svg_path = self.render_svg(notes)

        return png_bytes, svg_path
