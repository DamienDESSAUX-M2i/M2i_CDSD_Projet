import logging
from pathlib import Path

import pandas as pd

from src.utils import LOGGER_NAME


class CSVLoader:
    """Loader for a CSV file."""

    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)

    def load(self, df: pd.DataFrame, file_path: Path, **kwargs) -> None:
        """Load DataFrame to a CSV file.

        Args:
            df (pd.DataFrame): DataFrame to load.
            filepath (Path): Path of the CSV file.
        """
        try:
            self.logger.info("Attempting to load DataFrame.")
            df.to_csv(path_or_buf=file_path, index=False, **kwargs)
            self.logger.info(f"DataFrame loaded to : {file_path}.")
        except Exception as e:
            self.logger.error(f"Error CSV loader : {e}.")
            raise
