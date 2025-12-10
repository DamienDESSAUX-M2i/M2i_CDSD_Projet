import logging
from abc import ABC, abstractmethod

import pandas as pd

from src.extractors.abstract_extractor import AbstractExtractor
from src.loaders.abstract_loader import AbstractLoader
from src.transformers.abstract_transformer import AbstractTransformer


class AbstractETLPipeline(ABC):
    """Abstract ETL Pipeline."""

    def __init__(
        self,
        config,
        logger: logging.Logger,
        extractor: AbstractExtractor,
        transformer: AbstractTransformer,
        loader: AbstractLoader,
    ):
        self.config = config
        self.logger = logger
        self.extractor = extractor
        self.transformer = transformer
        self.loader = loader

    def run(self):
        """Run pipeline."""
        try:
            self.logger.info("=" * 50)
            self.logger.info("Start ETL pipeline.")
            self.logger.info("=" * 50)

            self.logger.info("[1/3] Extraction.")
            df: pd.DataFrame = self._extract()

            self.logger.info("[2/3] Transformation.")
            df_transformed: pd.DataFrame = self._transform(df)

            self.logger.info("[3/3] Loading.")
            self._load(df_transformed)

            self.logger.info("=" * 50)
            self.logger.info("Pipeline completed successfully.")
            self.logger.info("=" * 50)
        except Exception as e:
            self.logger.error(f"Pipeline Failed : {e}.")

    @abstractmethod
    def _extract(self):
        """Extraction process."""
        raise NotImplementedError

    @abstractmethod
    def _transform(self, df: pd.DataFrame):
        """Transformation process."""
        raise NotImplementedError

    @abstractmethod
    def _load(self, df: pd.DataFrame):
        """Loading process."""
        raise NotImplementedError
