import json
from pathlib import Path
from typing import Any

from src.loaders.abstract_loader import AbstractLoader


class JSONLoader(AbstractLoader):
    """Loader for a JSON file."""

    def load_csv(self, dict_data: dict[str, Any], file_path: Path, **kwargs) -> None:
        """Load dictionary to a JSON file.

        Args:
            dict_data (dict[str, Any]): Dictionary to load.
            filepath (Path): Path of the JSON file.
        """
        try:
            self.logger.info("Attempting to load dictionary.")
            with open(file=file_path, mode="w", encoding="utf-8") as file:
                json.dump(obj=dict_data, fp=file, **kwargs)
            self.logger.info(f"DataFrame loaded to : {file_path}.")
        except Exception as e:
            self.logger.error(f"Error JSON loader : {e}.")
            raise
