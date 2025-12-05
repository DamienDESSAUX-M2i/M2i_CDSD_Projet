from abc import ABC, abstractmethod
from typing import Any


class AbstractLoader(ABC):
    """Abstract class for loaders."""

    def __init__(self, logger):
        self.logger = logger

    @abstractmethod
    def load(self) -> Any:
        """Load data."""
        raise NotImplementedError
