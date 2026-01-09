import logging

from config import minio_config

from minio import Minio


def get_client() -> Minio:
    return Minio(
        endpoint=minio_config.minio_endpoint,
        access_key=minio_config.minio_root_user,
        secret_key=minio_config.minio_root_password,
        secure=minio_config.minio_secure,
    )


def make_buckets(logger: logging.Logger) -> None:
    try:
        logger.info("Attempting to connect to the MinIO service.")
        client: Minio = get_client()
        logger.info("Connecting to the MinIO service.")

        logger.info("Attempting to create buckets.")
        for bucket_name in [
            minio_config.bucket_raw,
            minio_config.bucket_processed,
            minio_config.bucket_output,
        ]:
            if not client.bucket_exists(bucket_name=bucket_name):
                client.make_bucket(bucket_name=bucket_name)
                logger.info(f"Bucket created : {bucket_name}")
            else:
                logger.info(f"Bucket {bucket_name} already exists.")
    except Exception as e:
        logger.error(f" Error MinIO make buckets: {e}.")
