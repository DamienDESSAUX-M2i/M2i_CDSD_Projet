import logging
from pathlib import Path

import matplotlib.axes
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import pretty_midi
from matplotlib.ticker import MultipleLocator

from .note_tracker import NoteEvent

logger = logging.getLogger(__name__)


class PianoRollRenderer:
    """
    Render MIDI note events into piano-roll visualizations.

    Supported output formats:
        - PNG raster image.
        - SVG vector image.

    The renderer expects note events expressed in MIDI pitch space
    with timestamps expressed in seconds.
    """

    def __init__(
        self,
        pitch_min: int = 40,
        pitch_max: int = 88,
        figsize: tuple[int, int] = (12, 7),
    ) -> None:
        """
        Initialize piano-roll renderer.

        Args:
            pitch_min:
                Lowest MIDI pitch displayed.

            pitch_max:
                Highest MIDI pitch displayed.

            figsize:
                Matplotlib figure size in inches.

        Raises:
            ValueError:
                If MIDI pitch bounds are invalid.
        """

        if not 0 <= pitch_min <= 127:
            raise ValueError(f"Invalid minimum MIDI pitch: {pitch_min}")

        if not 0 <= pitch_max <= 127:
            raise ValueError(f"Invalid maximum MIDI pitch: {pitch_max}")

        if pitch_min >= pitch_max:
            raise ValueError("pitch_min must be lower than pitch_max.")

        self._pitch_min = pitch_min
        self._pitch_max = pitch_max
        self._figsize = figsize

        logger.debug(
            "PianoRollRenderer initialized: pitch_range=%d-%d, figsize=%s",
            pitch_min,
            pitch_max,
            figsize,
        )

    def _create_figure(
        self,
        notes: list[NoteEvent],
    ) -> tuple[
        matplotlib.figure.Figure,
        matplotlib.axes.Axes,
    ]:
        """
        Create a Matplotlib piano-roll figure.

        Args:
            notes:
                Musical note events to display.

        Returns:
            Tuple containing the Matplotlib figure and axes.
        """

        fig, ax = plt.subplots(
            figsize=self._figsize,
            constrained_layout=True,
        )

        for note in notes:
            ax.broken_barh(
                xranges=[
                    (
                        note.start_time,
                        note.duration,
                    )
                ],
                yrange=(
                    note.pitch - 0.4,
                    0.8,
                ),
            )

        ax.set_xlabel(
            "Time (s)",
            fontsize=12,
        )

        ax.set_ylabel(
            "Pitch",
            fontsize=12,
        )

        ax.set_title(
            "Automatic Guitar Transcription",
            fontsize=14,
        )

        pitches = np.arange(
            self._pitch_min,
            self._pitch_max + 1,
        )

        ax.set_yticks(pitches)

        ax.set_yticklabels(
            [pretty_midi.note_number_to_name(pitch) for pitch in pitches],
            fontsize=8,
        )

        ax.set_ylim(
            self._pitch_min - 0.5,
            self._pitch_max + 0.5,
        )

        if notes:
            ax.set_xlim(
                0,
                max(note.end_time for note in notes),
            )

        ax.xaxis.set_major_locator(MultipleLocator(1.0))

        ax.xaxis.set_minor_locator(MultipleLocator(0.25))

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

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        return fig, ax

    def render_png(
        self,
        notes: list[NoteEvent],
        output_path: Path,
    ) -> None:
        """
        Render piano roll as PNG image.

        Args:
            notes:
                Musical note events.

            output_path:
                Destination PNG file path.
        """

        logger.debug(
            "Rendering piano roll PNG: notes=%d, path=%s",
            len(notes),
            output_path,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        fig, _ = self._create_figure(notes)

        try:
            fig.savefig(
                output_path,
                format="png",
                dpi=150,
                bbox_inches="tight",
            )

        finally:
            plt.close(fig)

        logger.info(
            "Piano roll PNG generated: %s",
            output_path,
        )

    def render_svg(
        self,
        notes: list[NoteEvent],
        output_path: Path,
    ) -> None:
        """
        Render piano roll as SVG vector image.

        Args:
            notes:
                Musical note events.

            output_path:
                Destination SVG file path.
        """

        logger.debug(
            "Rendering piano roll SVG: notes=%d, path=%s",
            len(notes),
            output_path,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        fig, _ = self._create_figure(notes)

        try:
            fig.savefig(
                output_path,
                format="svg",
                bbox_inches="tight",
            )

        finally:
            plt.close(fig)

        logger.info(
            "Piano roll SVG generated: %s",
            output_path,
        )

    def render(
        self,
        notes: list[NoteEvent],
        png_path: Path,
        svg_path: Path,
    ) -> None:
        """
        Generate all piano-roll visual outputs.

        Args:
            notes:
                Musical note events.

            png_path:
                Output path for PNG rendering.

            svg_path:
                Output path for SVG rendering.
        """

        logger.info(
            "Generating piano roll artifacts: notes=%d",
            len(notes),
        )

        self.render_png(notes=notes, output_path=png_path)

        self.render_svg(notes=notes, output_path=svg_path)

        logger.info("Piano roll rendering completed.")
