from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pretty_midi
from matplotlib.ticker import MultipleLocator

from .note_tracker import NoteEvent


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
        figsize: tuple[int, int] = (12, 7),
    ) -> None:
        """
        Initialize piano roll renderer.

        Args:
            pitch_min:
                Lowest MIDI pitch displayed.
            pitch_max:
                Highest MIDI pitch displayed.
            figsize:
                Matplotlib figure size.
        """

        self.pitch_min = pitch_min
        self.pitch_max = pitch_max
        self.figsize = figsize

    def _create_figure(
        self,
        notes: list[NoteEvent],
    ) -> tuple[plt.Figure, plt.Axes]:
        """
        Create a publication-quality piano roll figure.

        Args:
            notes:
                Detected note events.

        Returns:
            Matplotlib figure and axis.
        """

        fig, ax = plt.subplots(figsize=self.figsize, constrained_layout=True)

        # ====
        # Notes
        # ====

        for note in notes:
            ax.broken_barh(
                xranges=[(note.start_time, note.end_time - note.start_time)],
                yrange=(note.pitch - 0.4, 0.8),
            )

        # ====
        # Axes
        # ====

        ax.set_xlabel("Time (s)", fontsize=12)

        ax.set_ylabel("Pitch", fontsize=12)

        ax.set_title("Automatic Guitar Transcription", fontsize=14, pad=12)

        # ====
        # Pitch axis
        # ====

        pitches = np.arange(self.pitch_min, self.pitch_max + 1)

        ax.set_yticks(pitches)

        ax.set_yticklabels(
            [pretty_midi.note_number_to_name(p) for p in pitches], fontsize=8
        )

        ax.set_ylim(
            self.pitch_min - 0.5,
            self.pitch_max + 0.5,
        )

        # ====
        # Time axis
        # ====

        if notes:
            xmax = max(note.end_time for note in notes)

            ax.set_xlim(
                0,
                xmax,
            )

        ax.xaxis.set_major_locator(MultipleLocator(1.0))

        ax.xaxis.set_minor_locator(MultipleLocator(0.25))

        # ====
        # Grid
        # ====

        ax.grid(
            which="major",
            axis="x",
            linewidth=0.8,
            alpha=0.6,
        )

        ax.grid(
            which="minor",
            axis="x",
            linewidth=0.3,
            alpha=0.3,
        )

        ax.grid(
            which="major",
            axis="y",
            linewidth=0.2,
            alpha=0.25,
        )

        # ====
        # Clean style
        # ====

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.tick_params(
            axis="both",
            labelsize=9,
        )

        return fig, ax

    def render_png(
        self,
        notes: list[NoteEvent],
        output_path: Path,
    ) -> None:
        """
        Render piano roll as PNG.

        The image is also saved locally.

        Args:
            notes:
                Detected MIDI notes.
            output_path:
                Output path.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)

        fig, _ = self._create_figure(notes)

        fig.tight_layout()

        fig.savefig(
            output_path,
            format="png",
            dpi=150,
            bbox_inches="tight",
        )

        plt.close(fig)

    def render_svg(
        self,
        notes: list[NoteEvent],
        output_path: Path,
    ) -> None:
        """
        Render piano roll as SVG.

        Args:
            notes:
                Detected MIDI notes.
            output_path:
                Output path.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)

        fig, _ = self._create_figure(notes)

        fig.tight_layout()

        fig.savefig(
            output_path,
            format="svg",
            bbox_inches="tight",
        )

        plt.close(fig)

    def render(
        self,
        notes: list[NoteEvent],
        png_path: Path,
        svg_path: Path,
    ) -> None:
        """
        Render both PNG and SVG outputs.

        Args:
            notes:
                Detected MIDI notes.
            png_path:
                PNG output path.
            svg_path:
                SVG output path.
        """

        png_path = self.render_png(notes=notes, output_path=png_path)

        svg_path = self.render_svg(notes=notes, output_path=svg_path)
