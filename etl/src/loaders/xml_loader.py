import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from src.utils import LOGGER_NAME


class XMLLoader:
    """Loader for a XML file."""

    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)

    def load(self, tree: ET.ElementTree, file_path: Path, **kwargs) -> None:
        """Load ElementTree to a XML file.

        Args:
            tree (etree.ElementTree): ElementTree to load.
            file_path (Path): Path of the XML file.
        """
        try:
            self.logger.info("Attempting to load ElementTree.")
            tree.write(
                file_or_filename=file_path,
                encoding="utf-8",
                xml_declaration=True,
                **kwargs,
            )
            self.logger.info(f"ElementTree loaded to : {file_path}.")
        except Exception as e:
            self.logger.error(f"Error XML loader : {e}.")
            raise
