from __future__ import annotations

import logging
from abc import ABC, abstractmethod


class AbstractDatasetDownloader(ABC):
    """
    Abstract base class for dataset downloaders.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """
        Initialize the dataset downloader.

        Args:
            logger: Logger instance.
        """
        self.logger = logger

    @abstractmethod
    def download(self) -> None:
        """
        Execute the dataset download process.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError
