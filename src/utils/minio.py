import logging

from minio import Minio

from src.utils.config import minio_config


def get_client() -> Minio:
    return Minio(
        endpoint=minio_config.MINIO_ENDPOINT,
        access_key=minio_config.MINIO_ROOT_USER,
        secret_key=minio_config.MINIO_ROOT_PASSWORD,
        secure=False,
    )


def make_buckeks(logger: logging.Logger) -> None:
    try:
        logger.info("Attempting to connect to the MinIO service.")
        client: Minio = get_client()
        logger.info("Connecting to the MinIO service.")

        logger.info("Attempting to create buckets.")
        for bucket_name in [
            minio_config.BUCKET_BRONZE,
            minio_config.BUCKET_SILVER,
            minio_config.BUCKET_GOLD,
        ]:
            if not client.bucket_exists(bucket_name=bucket_name):
                client.make_bucket(bucket_name=bucket_name)
                logger.info(f"Bucket created : {bucket_name}")
            else:
                logger.info(f"Bucket {bucket_name} already exists.")
    except Exception as e:
        logger.error(f" Error MinIO make buckets: {e}.")
