import logging
from abc import ABC
from pathlib import Path

from src.utils import LOGGER_NAME


class AbstractExtractor(ABC):
    def __init__(self, logger_name: logging.Logger = LOGGER_NAME) -> None:
        self.logger = logging.getLogger(logger_name)

    def _validate_file_path(self, file_path: Path, suffix: str = None) -> None:
        """Raise an Exception if path is invalid."""
        if not isinstance(file_path, Path):
            raise ValueError("file_path must be a pathlib.Path.")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if suffix and (file_path.suffix.lower() != suffix):
            raise ValueError(
                f"Invalid file extension '{file_path.suffix}'. Expected '{suffix}'."
            )
