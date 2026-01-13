import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from src.utils import LOGGER_NAME


class XMLExtractor:
    """Extractor for a XML file."""

    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)

    def extract(self, file_path: Path, **kwargs) -> ET.ElementTree:
        """Extract data from a XML file.

        Args:
            file_path (Path): Path of the XML file.

        Returns:
            ET.Element: ElementTree extract from the XML file.
        """
        try:
            self.logger.info(f"Attempting to extract data from {file_path}.")
            tree = ET.parse(file_path, **kwargs)
            self.logger.info(f"Extraction completed : {tree}.")
            return tree
        except Exception as e:
            self.logger.error(f"Error XML extractor: {e}.")
            raise
