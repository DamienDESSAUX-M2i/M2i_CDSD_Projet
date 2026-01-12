import os
from dataclasses import dataclass


@dataclass
class MinIOConfig:
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    minio_user: str = os.getenv("MINIO_USER", "admin")
    minio_password: str = os.getenv("MINIO_PASSWORD", "admin0000")
    minio_secure: bool = os.getenv("MINIO_SECURE", False)
    bucket_raw: str = os.getenv("BUCKET_BRONZE", "raw")
    bucket_processed: str = os.getenv("BUCKET_SILVER", "processed")
    bucket_output: str = os.getenv("BUCKET_GOLD", "output")


minio_config = MinIOConfig()
