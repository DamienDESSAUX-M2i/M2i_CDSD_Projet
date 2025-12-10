import logging

import pandas as pd

from src.extractors.csv_extractor import CSVExtractor
from src.extractors.json_extractor import JSONExtractor
from src.extractors.minio_extractor import MinioExtractor
from src.loaders.csv_loader import CSVLoader
from src.loaders.json_loader import JSONLoader
from src.loaders.minio_loader import MinioLoader
from src.pipelines.abstract_etl_pipeline import AbstractETLPipeline


class ETLPipeline(AbstractETLPipeline):
    """ETL Pipeline."""

    def __init__(self, config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.minio_extractor = MinioExtractor(logger=self.logger)
        self.csv_extractor = CSVExtractor(logger=self.logger)
        self.json_extractor = JSONExtractor(logger=self.logger)
        self.minio_loader = MinioLoader(logger=self.logger)
        self.csv_loader = CSVLoader(logger=self.logger)
        self.json_loader = JSONLoader(logger=self.logger)

    def _extract(self):
        """Extraction process."""
        raise NotImplementedError

    def _transform(self, df: pd.DataFrame):
        """Transformation process."""
        raise NotImplementedError

    def _load(self, df: pd.DataFrame):
        """Loading process."""
        raise NotImplementedError
