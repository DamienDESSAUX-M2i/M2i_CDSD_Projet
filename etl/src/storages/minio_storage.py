import io
import json
import logging
from datetime import timedelta

from config import minio_config

from minio import Minio
from src.utils import LOGGER_NAME


class MinIOStorage:
    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.client = self._get_client()
        self._ensure_buckets()

    def _get_client(self) -> Minio:
        self.logger.info("Attempting to connect to the MinIO service.")
        client = Minio(
            endpoint=minio_config.minio_endpoint,
            access_key=minio_config.minio_user,
            secret_key=minio_config.minio_password,
            secure=minio_config.minio_secure,
        )
        self.logger.info("Connecting to the MinIO service.")
        return client

    def _ensure_buckets(self) -> None:
        """Check if buckets exist; if not, create them."""
        bucket_names = [
            minio_config.bucket_raw,
            minio_config.bucket_processed,
            minio_config.bucket_output,
        ]

        try:
            for bucket_name in bucket_names:
                if not self.client.bucket_exists(bucket_name):
                    self.logger.info(f"Bucket created: {bucket_name}")
                    self.client.make_bucket(bucket_name)
                else:
                    self.logger.info(f"Bucket {bucket_name} already exists.")
        except Exception as e:
            self.logger.error(f" Error MinIO make buckets: {e}.")

    def upload_export(
        self,
        bucket_name: str,
        file_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str | None:
        """Upload a file.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.
            data (bytes): File content.
            content_type (str, optional): MIME type. Defaults to "application/octet-stream".

        Returns:
            str | None: URI MinIO or None.
        """
        try:
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=file_name,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )

            uri = f"minio://{bucket_name}/{file_name}"
            self.logger.info(f"Export uploaded: {uri}")
            return uri

        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            return None

    def upload_json(self, bucket_name: str, file_name: str, data: dict) -> str | None:
        """Upload a JSON file.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.
            data (dict): Dictionary to dump in JSON format.

        Returns:
            str | None: URI MinIO or None.
        """
        json_bytes = json.dumps(
            obj=data, indent=4, ensure_ascii=False, default=str
        ).encode("utf-8")
        return self.upload_export(
            bucket_name=bucket_name,
            file_name=file_name,
            data=json_bytes,
            content_type="application/json",
        )

    # TODO
    def upload_xml(
        self, bucket_name: str, file_name: str, xml_content: str
    ) -> str | None:
        """Upload a XML file.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.
            xml_content (str): XML content.

        Returns:
            str | None: URI MinIO or None.
        """
        return self.upload_export(
            bucket_name=bucket_name,
            file_name=file_name,
            data=xml_content.encode("utf-8"),
            content_type="application/xml",
        )

    # TODO
    def upload_jams(
        self, bucket_name: str, file_name: str, jams_content: str
    ) -> str | None:
        """Upload a JAMS file.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.
            jams_content (str): JAMS content.

        Returns:
            str | None: URI MinIO or None.
        """
        return self.upload_export(
            bucket_name=bucket_name,
            file_name=file_name,
            data=jams_content.encode("utf-8"),
            content_type="application/jams",
        )

    def upload_image(
        self,
        bucket_name: str,
        file_name: str,
        image_data: bytes,
        content_type: str = "image/jpeg",
    ) -> str | None:
        """Upload an image.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.
            image_data (bytes): Image to upload.
            content_type (str, optional): MINE type. Defaults to "image/jpeg".

        Returns:
            str | None: MinIO URI or None.
        """
        try:
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=file_name,
                data=io.BytesIO(image_data),
                length=len(image_data),
                content_type=content_type,
            )

            uri = f"minio://{bucket_name}/{file_name}"
            self.logger.info(f"Image uploaded: {uri}")
            return uri

        except Exception as e:
            self.logger.error(f"Image upload failed: {e}")
            return None

    # TODO
    def upload_audio(
        self,
        bucket_name: str,
        file_name: str,
        audio_data: bytes,
        content_type: str = "audio/wav",
    ) -> str | None:
        """Upload an image.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.
            audio_data (bytes): Audio to upload.
            content_type (str, optional): MINE type. Defaults to "audio/wav".

        Returns:
            str | None: MinIO URI or None.
        """
        try:
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=file_name,
                data=io.BytesIO(audio_data),
                length=len(audio_data),
                content_type=content_type,
            )

            uri = f"minio://{bucket_name}/{file_name}"
            self.logger.info(f"Audio uploaded: {uri}")
            return uri

        except Exception as e:
            self.logger.error(f"Audio upload failed: {e}")
            return None

    def get_object(self, bucket_name: str, file_name: str) -> bytes | None:
        """Gets an object from a bucket using its file name.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.

        Returns:
            bytes | None: Object get or None.
        """
        try:
            response = self.client.get_object(bucket_name, file_name)
            data = response.read()
            response.close()
            response.release_conn()  # To reuse the connection
            self.logger.info(
                f"Object get: uri=minio://{bucket_name}/{file_name} size={len(data) // 8} octets"
            )
            return data
        except Exception as e:
            self.logger.info(f"Get object failed: {e}")
            return None

    def list_objects(self, bucket_name: str, prefix: str = "") -> list[dict]:
        """List of information about the objects in a bucket based on a prefix.

        Args:
            bucket_name (str): Bucket name.
            prefix (str, optional): Prefix. Defaults to "".

        Returns:
            list[dict]: List of information about the objects. Keys of dictionaries are "name" (str | None), "size" (int | None) and "modified" (datetime | None).
        """
        objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
        return [
            {"name": obj.object_name, "size": obj.size, "modified": obj.last_modified}
            for obj in objects
        ]

    def list_raws_audio(self) -> list[dict]:
        """List of information about the audio in the raw bucket.

        Returns:
            list[dict]: List of information about the audio in the raw bucket. Keys of dictionaries are "name" (str | None), "size" (int | None) and "modified" (datetime | None).
        """
        return self.list_objects(minio_config.bucket_raw, prefix="audio")

    def remove_object(self, bucket_name: str, file_name: str) -> bool:
        """Remove an object.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.

        Returns:
            bool: True if the object was successfully deleted, false otherwise.
        """
        try:
            self.client.remove_object(bucket_name, file_name)
            self.logger.info(f"Object removed: minio://{bucket_name}/{file_name}")
            return True
        except Exception as e:
            self.logger.error(f"Object remove error: {e}")
            return False

    def get_presigned_url(
        self, bucket_name: str, file_name: str, expires_hours: int = 24
    ) -> str | None:
        """Generates a pre-signed URL.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.
            expires_hours (int, optional): Number of hours before expiration. Defaults to 24.

        Returns:
            str | None: Pre-signed URL.
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=file_name,
                expires=timedelta(hours=expires_hours),
            )
            self.logger.info(
                f"Get presigned URL from minio://{bucket_name}/{file_name}"
            )
            return url
        except Exception as e:
            self.logger.error(f"Get presigned URL failed: {e}")
            return None

    def get_storage_stats(self) -> dict:
        """Storage statistics.

        Returns:
            dict: {"bucket_name": {"nb_objects": (int) number of objects, "total_size": (int) sum of objects size in bytes}, ...}
        """
        stats = {}

        bucket_names = [
            minio_config.bucket_raw,
            minio_config.bucket_processed,
            minio_config.bucket_output,
        ]

        for bucket_name in bucket_names:
            objects = self.list_objects(bucket_name)
            stats[bucket_name] = {
                "nb_objects": len(objects),
                "total_size": sum(o["size"] for o in objects),
            }

        return stats
