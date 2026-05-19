import logging
from abc import ABC


class AbstractStorage(ABC):
    """Base class for storage."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
