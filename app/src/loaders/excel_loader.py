from pathlib import Path
from typing import Any

import pandas as pd

from src.loaders import AbstractLoader


class ExcelLoader(AbstractLoader):
    """
    XLSX file loader.
    Load a dictionary of DataFrames to a XLSX file using the pandas backend.
    """

    def load(
        self, dict_dataframes: dict[str, pd.DataFrame], file_path: Path, **kwargs: Any
    ) -> None:
        """Load a dictionary of DataFrames to a XLSX file.

        Args:
            dict_dataframes (dict[str, pd.DataFrame]): Dictionary whose keys are the names of the sheets and whose values ​​are DataFrames to be loaded.
            file_path (Path): Destination path of the Excel file. Must end with '.xlsx'.
            **kwargs: Additional keyword arguments forwarded to 'pandas.DataFrame.to_excel'.

        Raises:
            TypeError: If inputs are of invalid type.
            ValueError: If the file path is invalid.
            RuntimeError: If writing the XLSX file fails.
        """
        self._load_validate_inputs(
            dict_dataframes=dict_dataframes,
            file_path=file_path,
        )
        self._ensure_parent_directory(parent_directory_path=file_path.parent)

        try:
            self.logger.info(
                "Writing WAV file",
                extra={
                    "path": str(file_path),
                    "sheet_names": list(dict_dataframes.keys()),
                    "shapes": [df.shape for df in dict_dataframes.values()],
                },
            )
            with pd.ExcelWriter(path=file_path) as writer:
                for sheet_name, df in dict_dataframes.items():
                    df.to_excel(
                        excel_writer=writer,
                        sheet_name=sheet_name,
                        index=False,
                        **kwargs,
                    )
                    self.logger.info(f"Written sheet: {sheet_name}")
            self.logger.info(
                "XLSX file successfully written",
                extra={
                    "path": str(file_path),
                },
            )
        except Exception as exc:
            self.logger.exception(
                "Failed to write XLSX file",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("WAV writing failed") from exc

    def _load_validate_inputs(
        self,
        dict_dataframes: dict[str, pd.DataFrame],
        file_path: Path,
    ) -> None:
        """Raise an exception if an input is invalid."""
        if not isinstance(dict_dataframes, dict):
            raise TypeError("dict_dataframes must be a dictionary")

        if not all(
            isinstance(sheet_name, str) and isinstance(df, pd.DataFrame)
            for sheet_name, df in dict_dataframes.items()
        ):
            raise TypeError(
                "dict_dataframes must have string keys and pandas DataFrame values"
            )
        if not isinstance(file_path, Path):
            raise TypeError("file_path must be a pathlib.Path.")
        if not file_path.suffix.lower() == ".xlsx":
            raise ValueError("file_path must end with '.xlsx'.")
