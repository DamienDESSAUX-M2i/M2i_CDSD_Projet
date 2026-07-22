import logging
from pathlib import Path
from xml.etree import ElementTree as ET

import verovio
from music21 import note, stream, tempo
from pypdf import PdfWriter

try:
    import cairosvg

    CAIROSVG_AVAILABLE = True
except Exception:
    CAIROSVG_AVAILABLE = False

from .rhythm_quantizer import QuantizedNoteEvent

logger = logging.getLogger(__name__)


class ScoreBuilder:
    """Generate and render musical scores.

    Processing pipeline:

        QuantizedNoteEvent
                |
                v
            music21 Score
                |
                v
            MusicXML
                |
                v
            Verovio rendering
                |
          +-----+------+
          |            |
          v            v
         SVG          PDF

    This class is responsible only for score generation and rendering.
    It does not perform rhythm quantization or note detection.
    """

    def build_musicxml(
        self,
        notes: list[QuantizedNoteEvent],
        output_path: Path,
        bpm: int = 120,
    ) -> None:
        """Create a MusicXML score from quantized note events.

        Args:
            notes:
                Quantized notes to insert into the score.

            output_path:
                Destination MusicXML file.

            bpm:
                Tempo marking inserted into the score.

        Raises:
            ValueError:
                If the note collection cannot be converted into a score.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Generating MusicXML score (%d notes, %d BPM).",
            len(notes),
            bpm,
        )

        score = stream.Score()
        part = stream.Part()  # type: ignore

        part.insert(0, tempo.MetronomeMark(number=bpm))

        for event in notes:
            musical_note = note.Note(event.pitch)

            musical_note.duration.quarterLength = event.duration

            part.insert(event.offset, musical_note)

        score.append(part)  # type: ignore

        score.write("musicxml", fp=output_path)  # type: ignore

        logger.info(
            "MusicXML generated: %s",
            output_path,
        )

    def render(
        self,
        musicxml_path: Path,
    ) -> tuple[Path | None, Path | None]:
        """Render a MusicXML file into SVG and PDF outputs.

        Args:
            musicxml_path:
                Source MusicXML document.

        Returns:
            Tuple containing:

                - PDF output path if cairosvg is available, otherwise None
                - SVG output path if cairosvg is available, otherwise None

        Raises:
            RuntimeError:
                If Verovio cannot load the MusicXML document.
        """

        if not CAIROSVG_AVAILABLE:
            return None, None

        output_dir = musicxml_path.parent

        svg_path = output_dir / f"{musicxml_path.stem}.svg"
        pdf_path = output_dir / f"{musicxml_path.stem}.pdf"

        logger.info(
            "Rendering score: %s",
            musicxml_path,
        )

        toolkit = verovio.toolkit()

        verovio_data_path = Path(verovio.__file__).parent / "data"

        logger.info(
            "Using Verovio resources: %s",
            verovio_data_path,
        )

        toolkit.setResourcePath(str(verovio_data_path))

        logger.info(
            "Bravura exists: %s",
            (verovio_data_path / "Bravura").exists(),
        )

        logger.info(
            "Leipzig exists: %s",
            (verovio_data_path / "Leipzig").exists(),
        )

        toolkit.setOptions(
            {
                "inputFrom": "xml",
                "pageWidth": 2100,
                "pageHeight": 2970,
                "scale": 40,
            }
        )

        if not toolkit.loadFile(str(musicxml_path)):
            logger.error(
                "Unable to load MusicXML file: %s",
                musicxml_path,
            )
            raise RuntimeError(f"Unable to load MusicXML file: {musicxml_path}")

        page_count = toolkit.getPageCount()

        logger.debug(
            "Rendering %d score page(s).",
            page_count,
        )

        svg_pages = self._render_svg_pages(toolkit, musicxml_path, page_count)

        pdf_pages = self._convert_svg_pages_to_pdf(svg_pages)

        self._merge_outputs(
            svg_pages=svg_pages,
            pdf_pages=pdf_pages,
            svg_output=svg_path,
            pdf_output=pdf_path,
        )

        logger.info(
            "Score rendering completed. PDF=%s SVG=%s",
            pdf_path,
            svg_path,
        )

        return pdf_path, svg_path

    @staticmethod
    def _render_svg_pages(
        toolkit: verovio.toolkit,
        musicxml_path: Path,
        page_count: int,
    ) -> list[Path]:
        """Render individual SVG pages using Verovio."""

        svg_pages: list[Path] = []

        for page_number in range(1, page_count + 1):
            page_path = (
                musicxml_path.parent / f"{musicxml_path.stem}_page_{page_number}.svg"
            )

            toolkit.renderToSVGFile(str(page_path), page_number)

            svg_pages.append(page_path)

        return svg_pages

    @staticmethod
    def _convert_svg_pages_to_pdf(
        svg_pages: list[Path],
    ) -> list[Path]:
        """Convert SVG pages into individual PDF files."""

        pdf_pages: list[Path] = []

        for svg_page in svg_pages:
            pdf_page = svg_page.with_suffix(".pdf")

            cairosvg.svg2pdf(url=str(svg_page), write_to=str(pdf_page))

            pdf_pages.append(pdf_page)

        return pdf_pages

    @staticmethod
    def _merge_outputs(
        svg_pages: list[Path],
        pdf_pages: list[Path],
        svg_output: Path,
        pdf_output: Path,
    ) -> None:
        """Merge generated pages into final artifacts."""

        if len(svg_pages) == 1:
            svg_pages[0].rename(svg_output)
        else:
            ScoreBuilder._merge_svgs(
                svg_pages,
                svg_output,
            )

        if len(pdf_pages) == 1:
            pdf_pages[0].rename(pdf_output)
        else:
            ScoreBuilder._merge_pdfs(
                pdf_pages,
                pdf_output,
            )

    @staticmethod
    def _merge_svgs(
        svg_files: list[Path],
        output: Path,
    ) -> None:
        """Merge multiple SVG pages into a single SVG document."""

        if not svg_files:
            raise ValueError("No SVG files provided.")

        logger.debug(
            "Merging %d SVG pages.",
            len(svg_files),
        )

        namespace = "http://www.w3.org/2000/svg"

        ET.register_namespace("", namespace)

        root = ET.parse(svg_files[0]).getroot()

        width = root.get("width")
        height = root.get("height")

        if width is None or height is None:
            raise ValueError("SVG dimensions are missing.")

        page_height = float(height.replace("px", ""))

        merged = ET.Element(
            f"{{{namespace}}}svg",
            {
                "width": width,
                "height": str(len(svg_files) * page_height),
                "viewBox": (
                    f"0 0 {width.replace('px', '')} {len(svg_files) * page_height}"
                ),
            },
        )

        for index, svg_file in enumerate(svg_files):
            page_root = ET.parse(svg_file).getroot()

            group = ET.Element(
                f"{{{namespace}}}g",
                {"transform": (f"translate(0,{index * page_height})")},
            )

            group.extend(page_root)
            merged.append(group)

        ET.ElementTree(merged).write(
            output,
            encoding="utf-8",
            xml_declaration=True,
        )

    @staticmethod
    def _merge_pdfs(
        pdf_files: list[Path],
        output: Path,
    ) -> None:
        """Merge multiple PDF pages into a single document."""

        logger.debug(
            "Merging %d PDF pages.",
            len(pdf_files),
        )

        writer = PdfWriter()

        for pdf_file in pdf_files:
            writer.append(str(pdf_file))

        with output.open("wb") as file:
            writer.write(file)
