import json
from pathlib import Path
from typing import Any

from src.loaders import AbstractLoader


class JSONLoader(AbstractLoader):
    """
    JSON file loader.
    Load data object to a JSON file.
    """

    def load(self, data: Any, file_path: Path, **kwargs: Any) -> None:
        """Load data to a JSON file.

        Args:
            data (Any): Data to load.
            file_path (Path): Destination path of the JSON file. Must end with '.json'.
            **kwargs: Additional keyword arguments forwarded to 'json.dump'.

        Raises:
            TypeError: If inputs are of invalid type.
            ValueError: If the file path is invalid.
            RuntimeError: If writing the JSON file fails.
        """
        self._load_validate_inputs(file_path=file_path)
        self._ensure_parent_directory(parent_directory_path=file_path.parent)

        try:
            self.logger.info(
                "Writing JSON file",
                extra={
                    "path": str(file_path),
                },
            )
            file_path.write_text(
                json.dump(obj=data, indent=4, ensure_ascii=False, **kwargs),
                encoding="utf-8",
            )
            self.logger.info(
                "JSON file successfully written",
                extra={
                    "path": str(file_path),
                },
            )
        except Exception as exc:
            self.logger.exception(
                "Failed to write JSON file",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("JSON writing failed") from exc

    def _load_validate_inputs(
        self,
        file_path: Path,
    ) -> None:
        """Raise an exception if an input is invalid."""
        if not isinstance(file_path, Path):
            raise TypeError("file_path must be a pathlib.Path.")
        if not file_path.suffix.lower() == ".json":
            raise ValueError("file_path must end with '.json'.")
