from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatasetsDownloaderSettings:
    """
    Configuration settings for dataset download operations.

    Attributes:
        chunk_size: Size, in bytes, of streamed chunks read from HTTP
            responses during downloads.

        timeout_seconds: Timeout applied to HTTP requests.

        max_retry_attempts: Maximum number of retry attempts for the
            overall download process.

        backoff_factor: Exponential backoff multiplier applied between
            global retry attempts.

        retry_total: Total number of HTTP-level retries handled by the
            underlying HTTP client.

        retry_backoff_factor: Backoff factor used by the HTTP retry
            strategy.

        retry_status_forcelist: HTTP status codes that trigger automatic
            retries.

        retry_allowed_methods: HTTP methods eligible for retry handling.

        token: Optional authentication token used for authenticated
            dataset sources.

        user_agent: User-Agent header value sent with HTTP requests.
    """

    chunk_size: int = 8_192
    timeout_seconds: int = 30

    max_retry_attempts: int = 3
    backoff_factor: float = 1.5

    retry_total: int = 3
    retry_backoff_factor: float = 1.5

    retry_status_forcelist: tuple[int, ...] = (500, 502, 503, 504)

    retry_allowed_methods: tuple[str, ...] = ("GET",)

    token: str | None = None
    user_agent: str = "DatasetDownloader/1.0"

    def __post_init__(self) -> None:
        """
        Validate downloader configuration values.

        Ensures all numeric parameters are valid and consistent in order
        to prevent runtime misconfiguration of dataset downloaders.

        Raises:
            ValueError: If a configuration value is invalid.
        """
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")

        if self.max_retry_attempts < 0:
            raise ValueError("max_retry_attempts must be >= 0")

        if self.backoff_factor < 0:
            raise ValueError("backoff_factor must be >= 0")

        if self.retry_total < 0:
            raise ValueError("retry_total must be >= 0")

        if self.retry_backoff_factor < 0:
            raise ValueError("retry_backoff_factor must be >= 0")


DATASETS_DOWNLOADER_SETTINGS = DatasetsDownloaderSettings()
