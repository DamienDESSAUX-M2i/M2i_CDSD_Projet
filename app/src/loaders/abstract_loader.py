import logging
from abc import ABC
from pathlib import Path

from src.utils import LOGGER_NAME


class AbstractLoader(ABC):
    def __init__(self, logger_name: logging.Logger = LOGGER_NAME) -> None:
        self.logger = logging.getLogger(logger_name)

    def _ensure_parent_directory(self, parent_directory_path: Path) -> None:
        if not parent_directory_path.exists():
            self.logger.info(
                "Creating parent directory",
                extra={"directory": str(parent_directory_path)},
            )
            parent_directory_path.mkdir(parents=True, exist_ok=True)
