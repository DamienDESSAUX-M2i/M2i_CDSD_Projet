import logging
from abc import ABC


class AbstractTransformer(ABC):
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
