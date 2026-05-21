import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MinIOSettings:
    minio_endpoint: str = (
        "localhost:9000"  # os.getenv("MINIO_ENDPOINT", "localhost:9000")
    )
    minio_user: str = os.getenv("MINIO_USER", "admin")
    minio_password: str = os.getenv("MINIO_PASSWORD", "admin0000")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    bucket_raw: str = os.getenv("BUCKET_BRONZE", "raw")
    bucket_processed: str = os.getenv("BUCKET_SILVER", "processed")
    bucket_output: str = os.getenv("BUCKET_GOLD", "output")


MINIO_SETTINGS = MinIOSettings()
