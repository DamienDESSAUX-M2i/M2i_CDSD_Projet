import logging
from pathlib import Path

import jams

from src.utils import LOGGER_NAME


class JAMSExtractor:
    """Extractor for a CSV file."""

    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)

    def extract(self, file_path: Path, **kwargs) -> jams.JAMS:
        """Extract data from a JAMS file.

        Args:
            file_path (Path): Path of the JAMS file.

        Returns:
            jams.JAMS: Data extract from the JAMS file.
        """
        try:
            self.logger.info(f"Attempting to extract data from {file_path}.")
            jam = jams.load(path_or_file=file_path, **kwargs)
            self.logger.info(f"Extraction completed : {jam.file_metadata}.")
            return jam
        except Exception as e:
            self.logger.error(f"Error JAMS extractor: {e}.")
            raise
