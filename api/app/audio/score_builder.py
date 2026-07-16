import logging
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
import verovio
from music21 import note, stream, tempo
from pypdf import PdfWriter

from .rhythm_quantizer import QuantizedNoteEvent

logger = logging.getLogger(__name__)


class ScoreBuilder:
    """
    Build and render musical scores.

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
            Verovio
                |
          +-----+------+
          |            |
          v            v
         PDF          SVG
    """

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

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

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

            part.insert(
                event.offset,
                current_note,
            )

        score.append(part)

        score.write("musicxml", fp=output_path)

        logger.info(f"MusicXML generated: {output_path}")

    def render(
        self,
        musicxml_path: Path,
    ) -> tuple[Path, Path]:
        """
        Render MusicXML into SVG and PDF.

        Args:
            musicxml_path:
                Input MusicXML file.

        Returns:
            Tuple containing:
                - SVG output path
                - PDF output path
        """

        output_dir = musicxml_path.parent

        svg_path = output_dir / f"{musicxml_path.stem}.svg"

        pdf_path = output_dir / f"{musicxml_path.stem}.pdf"

        verovio_toolkit = verovio.toolkit()

        verovio_toolkit.setOptions(
            {
                "inputFrom": "xml",
                "pageWidth": 2100,
                "pageHeight": 2970,
                "scale": 40,
            }
        )

        logger.info("Loading MusicXML into Verovio.")

        loaded = verovio_toolkit.loadFile(str(musicxml_path))

        if not loaded:
            raise RuntimeError(f"Unable to load {musicxml_path}")

        page_count = verovio_toolkit.getPageCount()

        logger.info(f"Rendering {page_count} page(s).")

        svg_pages: list[Path] = []
        for page_number in range(1, page_count + 1):
            page_svg = output_dir / f"{musicxml_path.stem}_page_{page_number}.svg"
            verovio_toolkit.renderToSVGFile(str(page_svg), page_number)
            svg_pages.append(page_svg)

        pdf_pages: list[Path] = []
        for svg_page in svg_pages:
            pdf_page = svg_page.with_suffix(".pdf")
            cairosvg.svg2pdf(url=str(svg_page), write_to=str(pdf_page))
            pdf_pages.append(pdf_page)

        # Merge SVG pages if necessary.
        if len(svg_pages) == 1:
            svg_pages[0].rename(svg_path)
        else:
            self._merge_pdfs(svg_pages, svg_path)

        # Merge PDF pages if necessary.
        if len(pdf_pages) == 1:
            pdf_pages[0].rename(pdf_path)
        else:
            self._merge_pdfs(pdf_pages, pdf_path)

        logger.info(f"PDF generated: {pdf_path}")

        logger.info(f"SVG generated: {svg_path}")

        return pdf_path, svg_path

    @staticmethod
    def _merge_svgs(
        svg_files: list[Path],
        output: Path,
    ) -> None:
        """
        Merge multiple SVG pages into one vertical SVG document.
        """

        if not svg_files:
            raise ValueError("No SVG files to merge")

        namespaces = {"svg": "http://www.w3.org/2000/svg"}

        ET.register_namespace("", namespaces["svg"])

        root = ET.parse(svg_files[0]).getroot()

        width = root.get("width")
        page_height = root.get("height")

        if width is None or page_height is None:
            raise ValueError("SVG dimensions missing")

        # Namespace cleaning
        root.tag = "{http://www.w3.org/2000/svg}svg"

        total_height = len(svg_files) * float(page_height.replace("px", ""))

        merged = ET.Element(
            "{http://www.w3.org/2000/svg}svg",
            {
                "width": width,
                "height": str(total_height),
                "viewBox": (f"0 0 {width.replace('px', '')} {total_height}"),
            },
        )

        for index, svg_file in enumerate(svg_files):
            page_root = ET.parse(svg_file).getroot()

            group = ET.Element(
                "{http://www.w3.org/2000/svg}g",
                {
                    "transform": (
                        f"translate(0,{index * float(page_height.replace('px', ''))})"
                    )
                },
            )

            for element in page_root:
                group.append(element)

            merged.append(group)

        tree = ET.ElementTree(merged)

        tree.write(
            output,
            encoding="utf-8",
            xml_declaration=True,
        )

    @staticmethod
    def _merge_pdfs(
        pdf_files: list[Path],
        output: Path,
    ) -> None:
        """
        Merge PDF pages.
        """

        pdf_writer = PdfWriter()

        for pdf_file in pdf_files:
            pdf_writer.append(str(pdf_file))

        with output.open("wb") as file:
            pdf_writer.write(file)
