import logging
from pathlib import Path

import pandas as pd

from src.utils import LOGGER_NAME


class ExcelLoader:
    """Loader for a EXCEL file."""

    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)

    def load(self, dict_dataframes: dict[str, pd.DataFrame], file_path: Path, **kwargs):
        """Load DataFrame to a Excel file.

        Args:
            dict_dataframes (dict[str, pd.DataFrame]): Dictionary whose keys are the names of the sheets and whose values ​​are DataFrames to be loaded.
            file_path (Path): Path of the Excel file.
        """
        try:
            self.logger.info("Attempting to load DataFrames.")
            with pd.ExcelWriter(path=file_path) as writer:
                for sheet_name, df in dict_dataframes.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False, **kwargs)
                    self.logger.info(f"\tWritten sheet : {sheet_name}")
            self.logger.info(f"DataFrames loaded to : {file_path}")
        except Exception as e:
            self.logger.error(f"EXCEL Loader Error : {e}")
            raise
