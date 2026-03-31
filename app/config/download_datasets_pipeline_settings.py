from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadDatasetsPipelineSettings:
    base_dir: str = "./app/data/raw"
    chunk_size: int = 8192
    timeout: int = 30
    max_retry_attempts: int = 5
    backoff_factor: float = 1.5
    retry_total: int = 3
    retry_backoff_factor: float = 1
    retry_status_forcelist: tuple[int, ...] = (500, 502, 503, 504)
    retry_allowed_methods: tuple[str, ...] = ("GET",)
    token: str | None = None
    user_agent: str = "DatasetDownloader/1.0"


download_datasets_pipeline_config = DownloadDatasetsPipelineSettings()
