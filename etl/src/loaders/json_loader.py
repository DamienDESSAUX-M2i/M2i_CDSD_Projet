import json
import logging
from pathlib import Path
from typing import Any

from src.utils import LOGGER_NAME


class JSONLoader:
    """Loader for a JSON file."""

    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)

    def load(self, data: list[dict[str, Any]], file_path: Path, **kwargs) -> None:
        """Load dictionary to a JSON file.

        Args:
            data (list[dict[str, Any]]): Dictionary to load.
            filepath (Path): Path of the JSON file.
        """
        try:
            self.logger.info("Attempting to load dictionary.")
            with open(file=file_path, mode="w", encoding="utf-8") as file:
                json.dump(obj=data, fp=file, **kwargs)
            self.logger.info(f"DataFrame loaded to : {file_path}.")
        except Exception as e:
            self.logger.error(f"Error JSON loader : {e}.")
            raise
