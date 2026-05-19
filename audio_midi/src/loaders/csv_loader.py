from pathlib import Path
from typing import Any

import pandas as pd

from src.loaders import AbstractLoader


class CSVLoader(AbstractLoader):
    """
    CSV file loader.
    Load a DataFrame to a CSV file using the pandas backend.
    """

    def load(self, df: pd.DataFrame, file_path: Path, **kwargs: Any) -> None:
        """Load a DataFrame to a CSV file

        Args:
            df (pd.DataFrame): DataFrame to load.
            filepath (Path): Destination path of the CSV file. Must be end with '.csv'.
            **kwargs: Additional keyword arguments forwarded to 'pd.DataFrame.to_csv'.

        Raises:
            TypeError: If inputs are of invalid type.
            ValueError: If the file path is invalid.
            RuntimeError: If writing the CSV file fails.
        """
        self._load_validate_inputs(
            df=df,
            file_path=file_path,
        )
        self._ensure_parent_directory(parent_directory_path=file_path.parent)

        try:
            self.logger.info(
                "Writing CSV file",
                extra={
                    "path": str(file_path),
                    "shape": df.shape,
                },
            )
            df.to_csv(path_or_buf=file_path, index=False, **kwargs)
            self.logger.info(
                "CSV file successfully written",
                extra={
                    "path": str(file_path),
                },
            )
        except Exception as exc:
            self.logger.exception(
                "Failed to write CSV file",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("CSV writing failed") from exc

    def _load_validate_inputs(
        self,
        df: pd.DataFrame,
        file_path: Path,
    ) -> None:
        """Raise an exception if an input is invalid."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a numpy pd.DataFrame.")
        if not isinstance(file_path, Path):
            raise TypeError("file_path must be a pathlib.Path.")
        if not file_path.suffix.lower() == ".csv":
            raise ValueError("file_path must end with '.csv'.")
