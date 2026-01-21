from dataclasses import dataclass
from pathlib import Path

import jams
import pandas as pd
from config import (
    guitar_set_ingestion_pipeline_config,
    minio_config,
    mongo_config,
    postgres_config,
)

from src.extractors import JAMSExtractor, WAVExtractor
from src.pipelines import AbstractPipeline


@dataclass
class GuitarSetIngestionPipelineStatistics:
    jams_loaded: int = 0
    jams_uploaded: int = 0
    jams_metadata_inserted: int = 0
    jams_annotation_inserted: int = 0
    jams_error: int = 0
    wav_loaded: int = 0
    wav_uploaded: int = 0
    wav_error: int = 0

    def to_dict(self) -> dict:
        """Cast the dataclass to a dictionary whose
        keys are attributes of the dataclass and
        values are values of the attributes."""
        return self.__dict__


class GuitarSetIngestionPipeline(AbstractPipeline):
    """Ingestion Pipeline."""

    def __init__(self, ingestion_limit: int | None = None):
        super().__init__()
        self.jams_extractor = JAMSExtractor()
        self.wav_extractor = WAVExtractor()
        self.ingestion_limit = (
            ingestion_limit or guitar_set_ingestion_pipeline_config.ingestion_limit
        )
        self.statistics = GuitarSetIngestionPipelineStatistics()

    def run(self):
        """Run pipeline.

        Raises:
            RuntimeError: If pipeline failed.
        """
        try:
            self.logger.info("Ingestion pipeline stars")

            self.logger.info("[1/2] JAMS ingestion")
            self._jams_ingestion()

            self.logger.info("[2/2] WAV ingestion")
            self._wav_ingestion()

            self.logger.info(
                f"Ingestion pipeline ends successfully: {self.statistics.to_dict()}"
            )
        except Exception as exc:
            self.logger.info("Ingestion pipeline failed.")
            raise RuntimeError("Ingestion pipeline failed") from exc

    def _jam_processing(self, jam_file_path: Path) -> None:
        """Processing of a jams.JAMS file.

        Args:
            jam_file_path (Path): Path of the JAMS file
        """
        try:
            jam = self.jams_extractor.load(file_path=jam_file_path)
            self.statistics.jams_loaded += 1

            self.minio_storage.upload_jams(
                bucket_name=minio_config.bucket_raw,
                file_name=f"{guitar_set_ingestion_pipeline_config.dataset_name}/{jam_file_path.stem}/annotation.jams",
                jam=jam,
            )
            self.statistics.jams_uploaded += 1

            jam_metadata = self.jams_extractor.extract_metadata(jam=jam)
            self.postgres_storage.insert_into_metadata(metadata=jam_metadata)
            self.statistics.jams_metadata_inserted += 1

            jam_annotation = self.jams_extractor.extract_annotation(jam=jam)
            self.statistics.jams_annotation_inserted += 1
        except Exception as exception:
            self.statistics.jams_error += 1
            self.logger.error(f"JAMS processing has failed: {exception}")

    def _jams_ingestion(self) -> None:
        """Ingestion of jams.JAMS files."""
        nb_ingestion = 1
        for jam_file_path in guitar_set_ingestion_pipeline_config.annotation_path.glob(
            "*.jams"
        ):
            self._jam_processing(jam_file_path=jam_file_path)
            if (
                self.ingestion_limit is not None
                and self.ingestion_limit <= nb_ingestion
            ):
                break
            nb_ingestion += 1

    def _wav_processing(self, wav_file_path: Path) -> None:
        """Processing of a WAV file.

        Args:
            wav_file_path (Path): Path of the WAV file

        Return:
            bool: True if
        """
        try:
            audio_data, sample_rate = self.wav_extractor.extract(
                file_path=wav_file_path
            )
            self.statistics.wav_loaded += 1

            self.minio_storage.upload_audio(
                bucket_name=minio_config.bucket_raw,
                file_name=f"{guitar_set_ingestion_pipeline_config.dataset_name}/{wav_file_path.stem}/audio_mono_pickup_mix.wav",
                audio_data=audio_data,
                sample_rate=sample_rate,
            )
            self.statistics.wav_uploaded += 1
        except Exception as exception:
            self.statistics.wav_error += 1
            self.logger.error(f"WAV processing has failed: {exception}")

    def _wav_ingestion(self) -> None:
        """Ingestion of WAV files."""
        nb_ingestion = 1
        for (
            wav_file_path
        ) in guitar_set_ingestion_pipeline_config.audio_mono_pickup_mix_path.glob(
            "*.wav"
        ):
            self._wav_processing(wav_file_path=wav_file_path)
            if (
                self.ingestion_limit is not None
                and self.ingestion_limit <= nb_ingestion
            ):
                break
            nb_ingestion += 1
