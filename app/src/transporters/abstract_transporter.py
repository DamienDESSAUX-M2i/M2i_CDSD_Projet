import logging
from abc import ABC

from src.utils import LOGGER_NAME


class AbstractTransporter(ABC):
    def __init__(self) -> None:
        self.logger = logging.getLogger(LOGGER_NAME)
