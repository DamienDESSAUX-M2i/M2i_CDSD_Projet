import logging
from abc import ABC, abstractmethod
from pathlib import Path


class AbstractLoader(ABC):
    """
    Base class for data loaders.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """
        Initialize the extractor.

        Args:
            logger: Logger instance.
        """

        self.logger = logger

    @abstractmethod
    def load(self, *args, **kwargs) -> None:
        """Load data method."""

        raise NotImplementedError

    def _ensure_parent_directory(self, parent_directory_path: Path) -> None:
        if not parent_directory_path.exists():
            self.logger.info(f"Creating parent directory: {str(parent_directory_path)}")
            parent_directory_path.mkdir(parents=True, exist_ok=True)
