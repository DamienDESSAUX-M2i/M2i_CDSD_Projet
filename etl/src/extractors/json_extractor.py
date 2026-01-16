import json
from pathlib import Path
from typing import Any

from src.extractors import AbstractExtractor


class JSONExtractor(AbstractExtractor):
    """
    JSON file extractor.
    Extract data from a JSON file using the pandas backend.
    """

    def extract(self, file_path: Path, **kwargs: Any) -> Any:
        """Extract data from a JSON file.

        Args:
            file_path (Path): Path of the Json file. Must end with '.json'.
            **kwargs: Additional keyword arguments forwarded to 'json.loads'.

        Raises:
            FileNotFoundError: If the JSON file does not exist.
            ValueError: If inputs are invalid.
            RuntimeError: If reading the JSON file fails.

        Returns:
            Any: Data extract from the JSON file.
        """
        self._validate_file_path(file_path=file_path, suffix=".json")

        try:
            self.logger.info(
                "Reading JSON file",
                extra={
                    "path": str(file_path),
                },
            )
            dict_data = json.loads(fp=file_path.read_text(encoding="utf-8"), **kwargs)
            self.logger.info(
                "JSON extraction completed",
                extra={
                    "path": str(file_path),
                },
            )
            return dict_data
        except Exception as exc:
            self.logger.exception(
                "Failed to load JSON file.",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("JSON extraction failed") from exc
