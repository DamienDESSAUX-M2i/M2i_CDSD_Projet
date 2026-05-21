import io
import json
import logging
import xml.etree.ElementTree as etree
from datetime import timedelta
from typing import Iterator

import jams
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import soundfile as sf
from minio.datatypes import Object
from minio.error import S3Error
from settings import MINIO_SETTINGS

from minio import Minio

from .abstract_storage import AbstractStorage


class MinIOStorage(AbstractStorage):
    """Storage backend implementation based on MinIO object storage.

    This class provides an abstraction layer for interacting with a MinIO
    service through the `minio` client SDK. It is responsible for:

    - Initializing the MinIO client connection
    - Verifying the availability of required buckets
    - Creating missing buckets automatically at startup
    - Managing object storage operations implemented in inherited methods

    The storage service relies on the application MinIO configuration defined
    in `MINIO_SETTINGS`.
    """

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)
        self.client = self._get_client()
        self._ensure_buckets()

    def _get_client(self) -> Minio:
        """Build a Minio client.

        Returns:
            Minio: A minio client.
        """

        self.logger.info("Connexion to the MinIO service...")
        client = Minio(
            endpoint=MINIO_SETTINGS.minio_endpoint,
            access_key=MINIO_SETTINGS.minio_user,
            secret_key=MINIO_SETTINGS.minio_password,
            secure=MINIO_SETTINGS.minio_secure,
        )
        self.logger.info("Connecting to the MinIO service")
        return client

    def _ensure_buckets(self) -> None:
        """Check if buckets exist; if not, create them."""

        bucket_names = [
            MINIO_SETTINGS.bucket_raw,
            MINIO_SETTINGS.bucket_processed,
            MINIO_SETTINGS.bucket_output,
        ]

        try:
            for bucket_name in bucket_names:
                if not self.client.bucket_exists(bucket_name):
                    self.logger.debug(f"Bucket created: {bucket_name}")
                    self.client.make_bucket(bucket_name)
                else:
                    self.logger.debug(f"Bucket {bucket_name} already exists.")
        except Exception as e:
            self.logger.error(f" Error MinIO make buckets: {e}.")

    def put_object(
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
            self.logger.debug(f"Uploaded completed: uri={uri}, bytes={len(data)}")
            return uri

        except S3Error as exception:
            self.logger.error(f"Upload has failed: {exception}")
            return None

    def put_json(self, bucket_name: str, file_name: str, data: dict) -> str | None:
        """Upload a JSON file.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.
            data (dict): Dictionary to dump in JSON format.

        Returns:
            str | None: URI MinIO or None.
        """

        self.logger.debug("Convert dictionary to JSON bytes...")
        json_bytes = json.dumps(
            obj=data, indent=4, ensure_ascii=False, default=str
        ).encode("utf-8")

        self.logger.debug("Upload JSON file...")
        return self.put_object(
            bucket_name=bucket_name,
            file_name=file_name,
            data=json_bytes,
            content_type="application/json",
        )

    def put_xml(
        self, bucket_name: str, file_name: str, tree: etree.ElementTree
    ) -> str | None:
        """Convert an ElemetTree to a XML file then upload the XML file.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.
            tree (etree.ElementTree): Tree to load.

        Returns:
            str | None: URI MinIO or None.
        """

        self.logger.debug("Convert ElementTree to XML bytes...")
        xml_bytes = etree.tostring(
            tree.getroot(), encoding="utf-8", xml_declaration=True
        )

        self.logger.debug("Upload XML file...")
        return self.put_object(
            bucket_name=bucket_name,
            file_name=file_name,
            data=xml_bytes,
            content_type="application/xml",
        )

    def put_jams(self, bucket_name: str, file_name: str, jam: jams.JAMS) -> str | None:
        """Upload a JAMS file.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.
            jam (jams.JAMS): JAMS class.

        Returns:
            str | None: URI MinIO or None.
        """

        self.logger.debug("Convert jams.JAMS to JSON bytes...")
        jam_bytes = jam.dumps(indent=4).encode("utf-8")

        self.logger.debug("Upload JAMS file...")
        return self.put_object(
            bucket_name=bucket_name,
            file_name=file_name,
            data=jam_bytes,
            content_type="application/jams",
        )

    def put_image(
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
            self.logger.debug("Upload image...")
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=file_name,
                data=io.BytesIO(image_data),
                length=len(image_data),
                content_type=content_type,
            )

            uri = f"minio://{bucket_name}/{file_name}"
            self.logger.debug(f"Image uploaded: {uri}")
            return uri

        except S3Error as exception:
            self.logger.error(f"Image upload failed: {exception}")
            return None

    def put_audio(
        self,
        bucket_name: str,
        file_name: str,
        audio_data: np.ndarray,
        sample_rate: int,
        content_type: str = "audio/wav",
    ) -> str | None:
        """Upload audio data as a WAV object to a MinIO bucket.

        Args:
            bucket_name (str): Target MinIO bucket name.
            file_name (str): Object name in the bucket (must end with .wav).
            audio_data (np.ndarray): Audio signal data. Shape must be (n_samples,) or (n_samples, n_channels).
            sample_rate (int): Sampling rate in Hz.
            content_type (str | None): MINE type. Defaults to "audio/wav".

        Returns:
            str | None: MinIO URI or None.
        """

        try:
            if not file_name.lower().endswith(".wav"):
                file_name = f"{file_name}.wav"

            self.logger.debug("Upload WAV...")
            buffer = io.BytesIO()

            sf.write(
                file=buffer,
                data=audio_data.T,  # Matrix translation because librosa: (n_channels, n_samples) and soundfile: (n_samples, n_channels).
                samplerate=sample_rate,
                format="WAV",
            )

            buffer.seek(0)  # Moves the buffer cursor to the beginning.
            data_size = buffer.getbuffer().nbytes

            self.client.put_object(
                bucket_name=bucket_name,
                object_name=file_name,
                data=buffer,
                length=data_size,
                content_type=content_type,
            )

            uri = f"minio://{bucket_name}/{file_name}"
            self.logger.debug(
                f"Uploading audio data to MinIO: uri={uri}, sample_rate={sample_rate}, shape={audio_data.shape}, bytes={data_size}"
            )
            return uri

        except S3Error as exception:
            self.logger.error(f"Audio upload failed: {exception}")
            return None

    def put_parquet(
        self,
        bucket_name: str,
        file_name: str,
        dataframe: pd.DataFrame,
    ) -> str | None:
        """
        Upload a Pandas DataFrame as a Parquet file to MinIO.

        Args:
            bucket_name: Target bucket
            file_name: Object name (.parquet recommended)
            dataframe: DataFrame to store

        Returns:
            MinIO URI or None
        """

        try:
            if not file_name.endswith(".parquet"):
                file_name = f"{file_name}.parquet"

            self.logger.debug("Converting DataFrame to Parquet...")

            buffer = io.BytesIO()

            table = pa.Table.from_pandas(dataframe)
            pq.write_table(table, buffer, compression="snappy")

            buffer.seek(0)
            size = buffer.getbuffer().nbytes

            self.client.put_object(
                bucket_name=bucket_name,
                object_name=file_name,
                data=buffer,
                length=size,
                content_type="application/octet-stream",
            )

            uri = f"minio://{bucket_name}/{file_name}"
            self.logger.debug(f"Parquet uploaded: {uri}, bytes={size}")
            return uri

        except Exception as e:
            self.logger.error(f"Parquet upload failed: {e}")
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
            self.logger.debug(
                f"Object get: uri=minio://{bucket_name}/{file_name}, bytes={len(data)}"
            )
            return data
        except S3Error as exception:
            self.logger.info(f"Get object failed: {exception}")
            return None

    def get_audio(
        self, bucket_name: str, file_name: str
    ) -> tuple[np.ndarray, int] | None:
        """Gets an audio from a bucket using its file name.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.

        Returns:
            tuple[np.ndarray, int] | None: A tuple containing audio_data, a numpy array of shape (n_samples,) or (n_samples, n_channels), and sample_rate, a sampling rate in Hz or None.
        """

        audio_bytes = self.get_object(
            bucket_name=bucket_name,
            file_name=file_name,
        )
        if len(audio_bytes) > 0:
            audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
            return (
                audio_data.T,  # Matrix translation because librosa: (n_channels, n_samples) and soundfile: (n_samples, n_channels)
                sample_rate,
            )
        return None

    def get_parquet(self, bucket_name: str, file_name: str) -> pd.DataFrame | None:
        """Load Parquet file from MinIO into a DataFrame.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.

        Returns:
            pd.DataFrame | None: Parquet file loaded into a DataFrame.
        """

        parquet_bytes = self.get_object(
            bucket_name=bucket_name,
            file_name=file_name,
        )
        if len(parquet_bytes) > 0:
            buffer = io.BytesIO(parquet_bytes)
            parquet = pq.read_table(buffer)
            return parquet.to_pandas()
        return None

    def list_objects(self, bucket_name: str, prefix: str = "") -> Iterator[Object]:
        """List of information about the objects in a bucket based on a prefix.

        Args:
            bucket_name (str): Bucket name.
            prefix (str, optional): Prefix. Defaults to "".

        Returns:
            Iterator[Object]: Iterator of minio.Object.
        """

        return self.client.list_objects(bucket_name, prefix=prefix, recursive=True)

    def list_raw(self, prefix: str = "") -> Iterator[Object]:
        """Iterator of minio.Object in the raw bucket.

        Args:
            prefix (str | None): Prefix. Defaults to "".

        Returns:
            Iterator[Object]: Iterator of minio.Object.
        """

        return self.list_objects(MINIO_SETTINGS.bucket_raw, prefix=prefix)

    def list_processed(self, prefix: str = "") -> Iterator[Object]:
        """Iterator of minio.Object in the processed bucket.

        Args:
            prefix (str | None): Prefix. Defaults to "".

        Returns:
            Iterator[Object]: Iterator of minio.Object.
        """

        return self.list_objects(MINIO_SETTINGS.bucket_processed, prefix=prefix)

    def list_output(self, prefix: str = "") -> Iterator[Object]:
        """Iterator of minio.Object in the output bucket.

        Args:
            prefix (str | None): Prefix. Defaults to "".

        Returns:
            Iterator[Object]: Iterator of minio.Object.
        """

        return self.list_objects(MINIO_SETTINGS.bucket_output, prefix=prefix)

    def remove_object(self, bucket_name: str, file_name: str) -> bool:
        """Remove an object.

        Args:
            bucket_name (str): Bucket name.
            file_name (str): File name.

        Returns:
            bool: True if the object was successfully deleted, false otherwise.
        """

        try:
            self.logger.debug("Remove object...")
            self.client.remove_object(bucket_name, file_name)
            self.logger.warning(
                f"Object removed: uri=minio://{bucket_name}/{file_name}"
            )
            return True
        except S3Error as exception:
            self.logger.error(f"Object remove has failed: {exception}")
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
            self.logger.debug("Get presigned URL...")
            url = self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=file_name,
                expires=timedelta(hours=expires_hours),
            )
            self.logger.debug(
                f"Presigned URL successfully created from minio://{bucket_name}/{file_name}"
            )
            return url
        except S3Error as exception:
            self.logger.error(f"Get presigned URL has failed: {exception}")
            return None

    def get_storage_stats(self) -> dict:
        """Storage statistics.

        Returns:
            dict: {"bucket_name": {"nb_objects": (int) number of objects, "total_size": (int) sum of objects size in bytes}, ...}
        """

        stats = {}

        bucket_names = [
            MINIO_SETTINGS.bucket_raw,
            MINIO_SETTINGS.bucket_processed,
            MINIO_SETTINGS.bucket_output,
        ]

        for bucket_name in bucket_names:
            list_objects = list(self.list_objects(bucket_name))
            stats[bucket_name] = {
                "nb_objects": len(list_objects),
                "total_size": sum(obj.size for obj in list_objects),
            }

        return stats
