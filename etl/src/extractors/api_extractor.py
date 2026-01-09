import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from src.utils import LOGGER_NAME


class APIExtractor:
    """Loader API REST."""

    def __init__(
        self,
        base_url: str,
        api_key: str = None,
        timeout: int = 30,
        retry_strategy: Retry = Retry(total=3, backoff_factor=1),
    ):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.retry_strategy = retry_strategy

    def extract(self, endpoint, params: dict[str, Any] = {}) -> requests.Response:
        """Extract data from API REST"""
        try:
            self.logger.info(f"Attempting request {self.base_url}/{endpoint}.")

            headers = {}
            if self.api_key:
                self.logger.info("API key place in the header.")
                headers["Authorization"] = f"Bearer {self.api_key}"

            with requests.Session() as session:
                adapter = HTTPAdapter(max_retries=self.retry_strategy)
                session.mount("http://", adapter)
                session.mount("https://", adapter)

                response = session.get(
                    url=f"{self.base_url}/{endpoint}",
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )

            response.raise_for_status()
            data = response.json()

            self.logger.info(f"Extraction completed : {len(data)} entries.")
            return data
        except Exception as e:
            self.logger.error(f"API Extractor Error : {e}")
            raise
