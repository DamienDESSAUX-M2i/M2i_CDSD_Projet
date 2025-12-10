from pathlib import Path

import pandas as pd

from src.loaders.abstract_loader import AbstractLoader


class CSVLoader(AbstractLoader):
    """Loader for a CSV file."""

    def load_csv(self, df: pd.DataFrame, file_path: Path, **kwargs) -> None:
        """Load DataFrame to a CSV file.

        Args:
            df (pd.DataFrame): DataFrame to load.
            filepath (Path): Path of the CSV file.
        """
        try:
            self.logger.info("Attempting to load DataFrame.")
            df.to_csv(path_or_buf=file_path, **kwargs)
            self.logger.info(f"DataFrame loaded to : {file_path}.")
        except Exception as e:
            self.logger.error(f"Error CSV loader : {e}.")
            raise
