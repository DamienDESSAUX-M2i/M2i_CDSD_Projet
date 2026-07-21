import json
from pathlib import Path
from typing import Any

from src.extractors import AbstractExtractor
from src.utils import validate_file_path


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

        validate_file_path(file_path=file_path, suffix=".json")

        try:
            self.logger.info(f"Reading JSON file: path={str(file_path)}")
            dict_data = json.loads(fp=file_path.read_text(encoding="utf-8"), **kwargs)
            self.logger.info(f"JSON extraction completed: path={str(file_path)}")
            return dict_data

        except Exception as exc:
            self.logger.exception(f"Failed to load JSON file: path={str(file_path)}")
            raise RuntimeError("JSON extraction failed") from exc
