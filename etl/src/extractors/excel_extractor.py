from pathlib import Path
from typing import Any

import pandas as pd

from src.extractors import AbstractExtractor


class ExcelExtractor(AbstractExtractor):
    """
    XLSX file extractor.
    Extract data from a XLSX file using the pandas backend.
    """

    def extract(self, file_path: Path, **kwargs: Any) -> dict[str, pd.DataFrame]:
        """Extract data from a XLSX file.

        Args:
            file_path (Path): Path of the XLSX file. Must end with '.xlsx'.
            **kwargs: Additional keyword arguments forwarded to 'pandas.read_excel'.

        Raises:
            FileNotFoundError: If the XLSX file does not exist.
            ValueError: If inputs are invalid.
            RuntimeError: If reading the XLSX file fails.

        Returns:
            dict[str, pd.DataFrame]: Dictionary whose keys are the names of the sheets and whose values ​​are the loaded DataFrames.
        """
        self._validate_file_path(file_path=file_path, suffix=".xlsx")

        try:
            self.logger.info(
                "Reading XLSX file",
                extra={
                    "path": str(file_path),
                },
            )
            dict_dfs = pd.read_excel(io=file_path, sheet_name=None, **kwargs)
            self.logger.info(
                "XLSX extraction completed",
                extra={
                    "path": str(file_path),
                    "sheet_names": list(dict_dfs.keys()),
                },
            )
            return dict_dfs
        except Exception as exc:
            self.logger.exception(
                "Failed to load CSV file.",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("CSV extraction failed") from exc
