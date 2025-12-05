from abc import ABC, abstractmethod
from typing import Any


class AbstractExtractor(ABC):
    """Abstract class for extractors."""

    def __init__(self, logger):
        self.logger = logger

    @abstractmethod
    def extract(self) -> Any:
        """Extract data."""
        raise NotImplementedError
