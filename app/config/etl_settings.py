from dataclasses import dataclass


@dataclass
class APIModel:
    base_url: str
    endpoint: str
    delay: float = 1.0
    timeout: int = 30
    max_retries: int = 3


@dataclass
class ETLConfig:
    api: APIModel


api = APIModel(
    base_url="https://jsonplaceholder.typicode.com",
    endpoint="posts",
)
etl_config = ETLConfig(
    api=api,
)
