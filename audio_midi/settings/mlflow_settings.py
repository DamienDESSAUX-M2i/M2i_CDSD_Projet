import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MLflowSettings:
    tracking_uri: str = "http://localhost:5000"  # os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    s3_endpoint_url: str = "http://localhost:9000"  # s3_endpoint_url=os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://localhost:9000")
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "admin")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "admin0000")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")


MLFLOW_SETTINGS = MLflowSettings()
