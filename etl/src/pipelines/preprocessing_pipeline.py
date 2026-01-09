import logging

from config import etl_config

from src.utils import LOGGER_NAME


class PreprocessingPipeline:
    """ETL Pipeline."""

    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)

    def _extract(self):
        """Extraction process."""
        pass

    def _transform(self, data):
        """Transformation process."""
        pass

    def _load(self, data_transformed):
        """Loading process."""
        pass
