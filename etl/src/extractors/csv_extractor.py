from pathlib import Path
from typing import Any

import pandas as pd

from src.extractors import AbstractExtractor


class CSVExtractor(AbstractExtractor):
    """
    CSV file extractor.
    Extract data from a CSV file using the pandas backend.
    """

    def extract(self, file_path: Path, **kwargs: Any) -> pd.DataFrame:
        """Extract data from a CSV file.

        Args:
            file_path (Path): Path of the CSV file. Must end with '.csv'.
            **kwargs: Additional keyword arguments forwarded to 'pandas.read_csv'.

        Raises:
            FileNotFoundError: If the CSV file does not exist.
            ValueError: If inputs are invalid.
            RuntimeError: If reading the CSV file fails.

        Returns:
            pd.DataFrame: DataFrame of the CSV file.
        """
        self._validate_file_path(file_path=file_path, suffix=".csv")

        try:
            self.logger.info(
                "Reading CSV file",
                extra={
                    "path": str(file_path),
                },
            )
            df: pd.DataFrame = pd.read_csv(filepath_or_buffer=file_path, **kwargs)
            self.logger.info(
                "WAV extraction completed",
                extra={
                    "path": str(file_path),
                    "shape": df.shape,
                },
            )
            return df
        except Exception as exc:
            self.logger.exception(
                "Failed to load CSV file.",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("CSV extraction failed") from exc
