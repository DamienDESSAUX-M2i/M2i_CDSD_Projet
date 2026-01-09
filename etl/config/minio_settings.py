import os

from pydantic_settings import BaseSettings


class MinIOConfig(BaseSettings):
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT")
    minio_root_user: str = os.getenv("MINIO_ROOT_USER")
    minio_root_password: str = os.getenv("MINIO_ROOT_PASSWORD")
    minio_secure: bool = os.getenv("MINIO_SECURE", False)
    bucket_raw: str = os.getenv("BUCKET_BRONZE", "raw")
    bucket_processed: str = os.getenv("BUCKET_SILVER", "processed")
    bucket_output: str = os.getenv("BUCKET_GOLD", "output")


minio_config = MinIOConfig()
