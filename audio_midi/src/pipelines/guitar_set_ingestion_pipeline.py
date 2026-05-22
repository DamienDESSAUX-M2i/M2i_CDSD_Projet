import logging
import re
from dataclasses import dataclass
from pathlib import Path

from settings import (
    GUITAR_SET_INGESTION_PIPELINE_SETTINGS,
    MINIO_SETTINGS,
)
from tqdm import tqdm

from src.extractors import JAMSExtractor, WAVExtractor
from src.models import AnnotationType
from src.pipelines import AbstractPipeline
from src.utils import Statistics

TITLE_REGEX = re.compile(
    r"(?P<title>\d{2}_[A-Za-z0-9]+-\d+-[A-G](?:b|\#)?_[A-Za-z]+)",
    re.VERBOSE,
)


@dataclass
class GuitarSetIngestionPipelineStatistics(Statistics):
    """Statistics container for GuitarSet ingestion pipeline.

    Attributes:
        jams_loaded: Number of JAMS files successfully loaded from the dataset.
        jams_uploaded: Number of JAMS files successfully uploaded to MinIO.
        recordings_inserted: Number of new recording rows inserted into PostgreSQL.
        recordings_updated: Number of existing recording rows updated in PostgreSQL.
        jams_metadata_inserted: Number of new GuitarSet metadata rows inserted into PostgreSQL.
        jams_metadata_updated: Number of existing GuitarSet metadata rows updated in PostgreSQL.
        jams_annotation_file_inserted: Number of new annotation file rows inserted into PostgreSQL.
        jams_annotation_file_updated: Number of existing annotation file rows updated in PostgreSQL.
        jams_annotation_inserted: Number of new annotation documents inserted into MongoDB.
        jams_annotation_updated: Number of existing annotation documents updated in MongoDB.
        jams_error: Number of errors encountered during JAMS ingestion and processing.
        wav_loaded: Number of WAV audio files successfully loaded from the dataset.
        wav_uploaded: Number of WAV audio files successfully uploaded to MinIO.
        audio_file_inserted: Number of new audio file rows inserted into PostgreSQL.
        audio_file_updated: Number of existing audio file rows updated in PostgreSQL.
        wav_error: Number of errors encountered during WAV ingestion and processing.
    """

    jams_loaded: int = 0
    jams_uploaded: int = 0
    recordings_inserted: int = 0
    recordings_updated: int = 0
    jams_metadata_inserted: int = 0
    jams_metadata_updated: int = 0
    jams_annotation_file_inserted: int = 0
    jams_annotation_file_updated: int = 0
    jams_annotation_inserted: int = 0
    jams_annotation_updated: int = 0
    jams_error: int = 0
    wav_loaded: int = 0
    wav_uploaded: int = 0
    audio_file_inserted: int = 0
    audio_file_updated: int = 0
    wav_error: int = 0


class GuitarSetIngestionPipeline(AbstractPipeline):
    """Ingestion Pipeline."""

    def __init__(self, logger: logging.Logger, ingestion_limit: int | None = None):
        super().__init__(logger)
        self.jams_extractor = JAMSExtractor(logger=self.logger)
        self.wav_extractor = WAVExtractor(logger=self.logger)
        self.ingestion_limit = (
            ingestion_limit or GUITAR_SET_INGESTION_PIPELINE_SETTINGS.ingestion_limit
        )
        self.statistics = GuitarSetIngestionPipelineStatistics()

    def run(self):
        """Run pipeline.

        Raises:
            RuntimeError: If pipeline failed.
        """

        try:
            self.logger.info("GuitarSet ingestion pipeline start...")

            self.logger.info("[1/2] JAMS ingestion")
            self._jams_ingestion(
                directory_jams_path=GUITAR_SET_INGESTION_PIPELINE_SETTINGS.annotation_path
            )

            self.logger.info("[2/2] WAV ingestion")
            self.logger.info("\t[1/4] Directory: audio_hex_pickup_debleeded")
            self._wav_ingestion(
                directory_wav_path=GUITAR_SET_INGESTION_PIPELINE_SETTINGS.audio_hex_pickup_debleeded_path
            )
            self.logger.info("\t[2/4] Directory: audio_hex_pickup_original_path")
            self._wav_ingestion(
                directory_wav_path=GUITAR_SET_INGESTION_PIPELINE_SETTINGS.audio_hex_pickup_original_path
            )
            self.logger.info("\t[3/4] Directory: audio_mono_mic_path")
            self._wav_ingestion(
                directory_wav_path=GUITAR_SET_INGESTION_PIPELINE_SETTINGS.audio_mono_mic_path
            )
            self.logger.info("\t[4/4] Directory: audio_mono_pickup_mix_path")
            self._wav_ingestion(
                directory_wav_path=GUITAR_SET_INGESTION_PIPELINE_SETTINGS.audio_mono_pickup_mix_path
            )

            self.logger.info(
                f"GuitarSet ingestion pipeline completed: {self.statistics.to_string()}"
            )
        except Exception as exception:
            self.logger.info(f"Ingestion pipeline has failed: {exception}")
            raise RuntimeError("Ingestion pipeline has failed") from exception

    def _jam_processing(self, jam_file_path: Path) -> None:
        """Processing of a jams.JAMS file.

        Args:
            jam_file_path (Path): Path of the JAMS file
        """

        try:
            # Load JAMS
            jam = self.jams_extractor.read(file_path=jam_file_path)
            self.statistics.jams_loaded += 1

            # Strore raw JAMS (MinIO)
            jam_uri = self.minio_storage.put_jams(
                bucket_name=MINIO_SETTINGS.bucket_raw,
                file_name=(
                    f"{GUITAR_SET_INGESTION_PIPELINE_SETTINGS.dataset_name}/"
                    f"{jam_file_path.stem}/annotation.jams"
                ),
                jam=jam,
            )

            if jam_uri is None:
                self.logger.error(
                    f"Failed to upload JAMS file to MinIO: {jam_file_path}"
                )
                raise

            self.statistics.jams_uploaded += 1

            # Extract metadata and annotations
            jam_metadata, annotations = self.jams_extractor.extract(jam=jam)
            jam_metadata = self.jams_extractor.enrich_with_directory_name(
                jam_metadata=jam_metadata, jam_file_path=jam_file_path
            )

            # Upsert recording (PostgreSQL)
            recording = self.postgres_storage.select_recording(
                dataset_name=jam_metadata.dataset_name, title=jam_metadata.title
            )

            if recording is None:
                recording = self.postgres_storage.insert_recording(
                    dataset_name=jam_metadata.dataset_name,
                    title=jam_metadata.title,
                )
                if recording is None:
                    self.logger.error(
                        f"Failed to insert recording to PostgreSQL: {jam_file_path}"
                    )
                    raise
                self.statistics.recordings_inserted += 1

            else:
                recording = self.postgres_storage.update_recording(
                    id_recording=recording["id_recording"],
                    dataset_name=jam_metadata.dataset_name,
                    title=jam_metadata.title,
                )
                if recording is None:
                    self.logger.error(
                        f"Failed to update recording to PostgreSQL: {jam_file_path}"
                    )
                    raise
                self.statistics.recordings_updated += 1

            id_recording = recording["id_recording"]

            # Upsert annotation_file (PostgreSQL)
            annotation_file = self.postgres_storage.select_annotation_file(
                id_recording=id_recording, annotation_type=AnnotationType.JAMS
            )

            if annotation_file is None:
                result = self.postgres_storage.insert_annotation_file(
                    id_recording=id_recording,
                    annotation_type=AnnotationType.JAMS,
                    uri=jam_uri,
                )
                if result is None:
                    self.logger.error(
                        f"Failed to insert annotation_file to PostgreSQL: {jam_file_path}"
                    )
                    raise
                self.statistics.jams_annotation_file_inserted += 1

            else:
                result = self.postgres_storage.update_annotation_file(
                    id_annotation=annotation_file["id_annotation"],
                    annotation_type=AnnotationType.JAMS,
                    uri=jam_uri,
                )
                if result is None:
                    self.logger.error(
                        f"Failed to update annotation_file to PostgreSQL: {jam_file_path}"
                    )
                    raise
                self.statistics.jams_annotation_file_updated += 1

            # Upsert guitarset_metadata (PostgreSQL)
            guitars_set_metadata = self.postgres_storage.select_guitarset_metadata(
                id_recording=id_recording
            )

            if guitars_set_metadata is None:
                result = self.postgres_storage.insert_guitarset_metadata(
                    id_recording=id_recording,
                    metadata=jam_metadata,
                )
                if result is None:
                    self.logger.error(
                        f"Failed to insert guitarset_metadata to PostgreSQL: {jam_file_path}"
                    )
                    raise
                self.statistics.jams_metadata_inserted += 1

            else:
                result = self.postgres_storage.update_guitarset_metadata(
                    id_recording=id_recording,
                    metadata=jam_metadata,
                )
                if result is None:
                    self.logger.error(
                        f"Failed to update guitarset_metadata to PostgreSQL: {jam_file_path}"
                    )
                    raise
                self.statistics.jams_metadata_updated += 1

            # Insert annotation_midi (Mongo)
            dict_annotation = annotations.to_dict()

            result = self.mongo_storage.insert_note_midi(
                note_midi=dict_annotation["note_midi"]
            )
            if result == "inserted":
                self.statistics.jams_annotation_inserted += 1
            elif result == "updated":
                self.statistics.jams_annotation_updated += 1
            else:
                self.logger.error(
                    f"Failed to insert annotation to MongoDB: {jam_file_path}"
                )
                raise

        except Exception as exception:
            self.statistics.jams_error += 1
            self.logger.error(f"JAMS processing has failed: {exception}")

    def _jams_ingestion(self, directory_jams_path: Path) -> None:
        """Ingestion of jams.JAMS files.

        Args:
            directory_jams_path (Path): Path of the directory containing JAMS files.
        """

        self.logger.debug("JAMS ingestion...")

        if not directory_jams_path.exists():
            raise FileNotFoundError(
                f"Directory does not exist: path={directory_jams_path}"
            )

        jams_paths = list(directory_jams_path.glob("*.jams"))
        if self.ingestion_limit is not None:
            jams_paths = jams_paths[: self.ingestion_limit]

        nb_ingestion = 0
        for jam_file_path in tqdm(
            jams_paths,
            desc="jAMS ingestion",
            colour="green",
        ):
            self._jam_processing(jam_file_path=jam_file_path)
            nb_ingestion += 1

        self.logger.debug(f"JANS ingestion completed: nb_ingestion={nb_ingestion}")

    def _wav_processing(self, wav_file_path: Path) -> None:
        """Processing of a WAV file.

        Args:
            wav_file_path (Path): Path of the WAV file
        """

        try:
            # Load audio
            audio_data, sample_rate = self.wav_extractor.extract(
                file_path=wav_file_path
            )
            self.statistics.wav_loaded += 1

            # Extract title
            title_match = TITLE_REGEX.match(wav_file_path.stem)
            if not title_match:
                self.logger.error(
                    f"Failed to extract title from file name: {wav_file_path.stem}"
                )
                raise

            title = title_match.group("title")

            # Fetch recording (PostgreSQL)
            recording = self.postgres_storage.select_recording(
                dataset_name=GUITAR_SET_INGESTION_PIPELINE_SETTINGS.dataset_name,
                title=title,
            )

            if recording is None:
                self.logger.error(f"Recording not found for WAV file: {wav_file_path}")
                raise

            id_recording = recording["id_recording"]

            # Store audio (MinIO)
            audio_type = wav_file_path.parent.name

            audio_uri = self.minio_storage.put_audio(
                bucket_name=MINIO_SETTINGS.bucket_raw,
                file_name=(
                    f"{GUITAR_SET_INGESTION_PIPELINE_SETTINGS.dataset_name}/"
                    f"{title}/{audio_type}.wav"
                ),
                audio_data=audio_data,
                sample_rate=sample_rate,
            )

            if audio_uri is None:
                self.logger.error(
                    f"Failed to upload WAV file to MinIO: {wav_file_path}"
                )
                raise

            self.statistics.wav_uploaded += 1

            # Upsert audio_file (PostgreSQL)
            audio_file = self.postgres_storage.select_audio_file(
                id_recording=id_recording,
                audio_type=audio_type,
            )

            if audio_file is None:
                result = self.postgres_storage.insert_audio_file(
                    id_recording=id_recording,
                    audio_type=audio_type,
                    uri=audio_uri,
                    sample_rate=sample_rate,
                    channels=audio_data.shape[1] if audio_data.ndim > 1 else 1,
                )

                if result is None:
                    self.logger.error(
                        f"Failed to insert audio_file to PostgreSQL: {wav_file_path}"
                    )
                    raise
                self.statistics.audio_file_inserted += 1

            else:
                result = self.postgres_storage.update_audio_file(
                    id_audio=audio_file["id_audio"],
                    audio_type=audio_type,
                    uri=audio_uri,
                    sample_rate=sample_rate,
                    channels=audio_data.shape[1] if audio_data.ndim > 1 else 1,
                )

                if result is None:
                    self.logger.error(
                        f"Failed to insert audio_file to PostgreSQL: {wav_file_path}"
                    )
                    raise
                self.statistics.audio_file_updated += 1

        except Exception as exception:
            self.statistics.wav_error += 1
            self.logger.error(f"WAV processing has failed: {exception}")

    def _wav_ingestion(self, directory_wav_path: Path) -> None:
        """Ingestion of WAV files.

        Args:
            directory_wav_path (Path): Path of the directory containing WAV files.
        """
        self.logger.debug("WAV ingestion...")

        if not directory_wav_path.exists():
            raise FileNotFoundError(
                f"Directory does not exist: path={directory_wav_path}"
            )

        wav_paths = list(directory_wav_path.glob("*.wav"))
        if self.ingestion_limit is not None:
            wav_paths = wav_paths[: self.ingestion_limit]

        nb_ingestion = 0
        for wav_file_path in tqdm(
            wav_paths,
            desc="WAV ingestion",
            colour="green",
        ):
            self._wav_processing(wav_file_path=wav_file_path)
            nb_ingestion += 1

        self.logger.debug(f"WAV ingestion completed: nb_ingestion={nb_ingestion}")
