import os
from pathlib import Path

from dotenv import load_dotenv
from minio import Minio

dotenv_path = Path("./config/minio.env")
load_dotenv(dotenv_path)

ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
ENDPOINT = os.getenv("MINIO_ENDPOINT")


def client():
    return Minio(
        endpoint=ENDPOINT, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False
    )
