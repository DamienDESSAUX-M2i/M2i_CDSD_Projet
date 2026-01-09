import logging

import pandas as pd
from src.extractors.api_extractor import APIExtractor
from src.extractors.csv_extractor import CSVExtractor
from src.extractors.excel_extractor import ExcelExtractor
from src.extractors.json_extractor import JSONExtractor
from src.extractors.minio_extractor import MinioExtractor
from src.extractors.postgresql_extractor import PostgreSQLExtractor
from src.loaders.csv_loader import CSVLoader
from src.loaders.excel_loader import ExcelLoader
from src.loaders.json_loader import JSONLoader
from src.loaders.minio_loader import MinioLoader
from src.loaders.postgresql_loader import PostgreSQLLoader
from src.pipelines.abstract_etl_pipeline import AbstractETLPipeline
from src.utils.config import ETLConfig


class ETLPipeline(AbstractETLPipeline):
    """ETL Pipeline."""

    def __init__(self, config: ETLConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.minio_extractor = MinioExtractor(logger=self.logger)
        self.csv_extractor = CSVExtractor(logger=self.logger)
        self.json_extractor = JSONExtractor(logger=self.logger)
        self.excel_extractor = ExcelExtractor(logger=logger)
        self.api_extractor = APIExtractor(
            logger=logger, base_url=self.config.api.base_url
        )
        self.postgresql_extractor = PostgreSQLExtractor(logger=self.logger)
        self.minio_loader = MinioLoader(logger=self.logger)
        self.csv_loader = CSVLoader(logger=self.logger)
        self.json_loader = JSONLoader(logger=self.logger)
        self.excel_loader = ExcelLoader(logger=logger)
        self.postgresql_loader = PostgreSQLLoader(logger=self.logger)

    def _extract(self):
        """Extraction process."""
        pass

    def _transform(self, df: pd.DataFrame):
        """Transformation process."""
        pass

    def _load(self, df: pd.DataFrame):
        """Loading process."""
        pass
