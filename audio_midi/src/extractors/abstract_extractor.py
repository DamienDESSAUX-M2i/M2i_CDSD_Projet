import logging
from abc import ABC, abstractmethod
from typing import Any


class AbstractExtractor(ABC):
    """
    Base class for data extractors.
    """

    def __init__(
        self,
        logger: logging.Logger,
    ) -> None:
        """
        Initialize the extractor.

        Args:
            logger: Logger instance.
        """

        self.logger = logger

    @abstractmethod
    def extract(self, *args, **kwargs) -> Any:
        """
        Extract data from a given input source.

        Returns:
            The extracted data in an implementation-defined format.
        """

        raise NotImplementedError
