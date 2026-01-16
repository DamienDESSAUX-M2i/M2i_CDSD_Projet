import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from src.extractors import AbstractExtractor


class XMLExtractor(AbstractExtractor):
    """
    XML file extractor.
    Extract data from a XML file using the xml backend.
    """

    def extract(self, file_path: Path, **kwargs: Any) -> ET.ElementTree:
        """Extract data from a XML file.

        Args:
            file_path (Path): Path to the XML file. Must end with '.xml'.
            **kwargs: Additional keyword arguments forwarded to 'xml.etree.ElementTree.ElementTree.parse'.

        Raises:
            FileNotFoundError: If the XML file does not exist.
            ValueError: If inputs are invalid.
            RuntimeError: If reading the XML file fails.

        Returns:
            ET.Element: ElementTree extract from the XML file.
        """
        self._validate_file_path(file_path=file_path, suffix=".xml")

        try:
            self.logger.info(
                "Reading XML file",
                extra={
                    "path": str(file_path),
                },
            )
            tree = ET.parse(file_path, **kwargs)
            self.logger.info(
                "XML extraction completed",
                extra={
                    "path": str(file_path),
                },
            )
            return tree
        except Exception as exc:
            self.logger.exception(
                "Failed to load XML file.",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("XML extraction failed") from exc
