import logging
from pathlib import Path

import pandas as pd

from src.utils import LOGGER_NAME


class CSVExtractor:
    """Extractor for a CSV file."""

    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)

    def extract(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Extract data from a CSV file.

        Args:
            file_path (Path): Path of the CSV file.

        Returns:
            pd.DataFrame: Data extract from the CSV file.
        """
        try:
            self.logger.info(f"Attempting to extract data from {file_path}.")
            df = pd.read_csv(filepath_or_buffer=file_path, **kwargs)
            self.logger.info(f"Extraction completed : {len(df)} lignes extract.")
            return df
        except Exception as e:
            self.logger.error(f"Error CSV extractor: {e}.")
            raise
