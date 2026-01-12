import logging
from pathlib import Path

import jams

from src.utils import LOGGER_NAME


class JAMSLoader:
    """Loader for a JAMS file."""

    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)

    def load(self, jam: jams.JAMS, file_path: Path, **kwargs) -> None:
        """Load jams.JAMS to a JAMS file.

        Args:
            jam (jams.JAMS): JAMS to load.
            file_path (Path): Path of the JAMS file.
        """
        try:
            self.logger.info("Attempting to load JAMS.")
            with open(file_path, mode="wt", encoding="utf-8") as f:
                f.write(jam.dumps())
            self.logger.info(f"JAMS loaded to : {file_path}.")
        except Exception as e:
            self.logger.error(f"Error JAMS loader : {e}.")
            raise
