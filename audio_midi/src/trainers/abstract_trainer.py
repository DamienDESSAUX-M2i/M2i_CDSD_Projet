import logging
from abc import ABC

from src.utils import LOGGER_NAME


class AbstractTrainer(ABC):
    def __init__(self, logger_name: logging.Logger = LOGGER_NAME) -> None:
        self.logger = logging.getLogger(logger_name)
