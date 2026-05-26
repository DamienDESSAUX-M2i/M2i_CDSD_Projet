import logging
from dataclasses import dataclass
from pathlib import Path

from settings import (
    IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS,
    MINIO_SETTINGS,
)
from tqdm import tqdm

from src.extractors import WAVExtractor, XMLExtractor
from src.models import AnnotationType, AudioType
from src.pipelines import AbstractPipeline
from src.utils import Statistics


@dataclass
class IDMTSMTGuitarIngestionPipelineStatistics(Statistics):
    """Statistics container for IDMT-SMT-Guitar ingestion pipeline.

    Attributes:
        xml_loaded: Number of XML files successfully loaded from the dataset.
        xml_error: Number of errors encountered during XML ingestion and processing.
        xml_uploaded: Number of xML files successfully uploaded to MinIO.
        recordings_inserted: Number of new recording rows inserted into PostgreSQL.
        recordings_updated: Number of existing recording rows updated in PostgreSQL.
        idmt_smt_guitar_metadata_inserted: Number of new IDMT-SMT-Guitar metadata rows inserted into PostgreSQL.
        idmt_smt_guitar_metadata_updated: Number of existing IDMT-SMT-Guitar metadata rows updated in PostgreSQL.
        annotation_file_inserted: Number of new annotation file rows inserted into PostgreSQL.
        annotation_file_updated: Number of existing annotation file rows updated in PostgreSQL.
        xml_annotation_inserted: Number of new annotation documents inserted into MongoDB.
        xml_annotation_updated: Number of existing annotation documents updated in MongoDB.
        wav_loaded: Number of WAV audio files successfully loaded from the dataset.
        wav_error: Number of errors encountered during WAV ingestion and processing.
        wav_uploaded: Number of WAV audio files successfully uploaded to MinIO.
        audio_file_inserted: Number of new audio file rows inserted into PostgreSQL.
        audio_file_updated: Number of existing audio file rows updated in PostgreSQL.
    """

    # WML metrics
    xml_loaded: int = 0
    xml_error: int = 0
    xml_uploaded: int = 0
    recordings_inserted: int = 0
    recordings_updated: int = 0
    idmt_smt_guitar_metadata_inserted: int = 0
    idmt_smt_guitar_metadata_updated: int = 0
    annotation_file_inserted: int = 0
    annotation_file_updated: int = 0
    xml_annotation_inserted: int = 0
    xml_annotation_updated: int = 0

    # Wav metrics
    wav_loaded: int = 0
    wav_error: int = 0
    wav_uploaded: int = 0
    audio_file_inserted: int = 0
    audio_file_updated: int = 0


class IDMTSMTGuitarIngestionPipeline(AbstractPipeline):
    """Ingestion Pipeline."""

    def __init__(
        self,
        logger: logging.Logger,
        ingestion_limit: int | None = None,
        dataset1: bool = True,
        dataset2: bool = True,
        dataset3: bool = True,
        dataset4: bool = True,
    ):
        super().__init__(logger)
        self.xml_extractor = XMLExtractor(logger=logger)
        self.wav_extractor = WAVExtractor(logger=logger)
        self.ingestion_limit = (
            ingestion_limit
            or IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS.ingestion_limit
        )
        self.dataset1 = dataset1
        self.dataset2 = dataset2
        self.dataset3 = dataset3
        self.dataset4 = dataset4
        self.statistics = IDMTSMTGuitarIngestionPipelineStatistics()

    def run(self):
        """Run pipeline.

        Raises:
            RuntimeError: If pipeline failed.
        """
        try:
            self.logger.info("IDMT SMT Guitar ingestion pipeline start...")

            if self.dataset1:
                self.logger.info("Ingestion of subset number 1...")
                self._dataset1_ingestion()

            if self.dataset2:
                self.logger.info("Ingestion of subset number 2...")
                self._dataset_ingestion(
                    dataset_path=IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS.dataset2_path,
                    dataset_number=2,
                )

            if self.dataset3:
                self.logger.info("Ingestion of subset number 3...")
                self._dataset_ingestion(
                    dataset_path=IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS.dataset3_path,
                    dataset_number=3,
                )

            if self.dataset4:
                self.logger.info("Ingestion of subset number 4...")
                self._dataset4_ingestion()

            self.logger.info(
                f"IDMT SMT Guitar ingestion pipeline ends successfully: {self.statistics.to_string()}"
            )
        except Exception as exc:
            self.logger.error("IDMT SMT Guitar ingestion pipeline failed.")
            raise RuntimeError("IDMT SMT Guitar ingestion pipeline failed") from exc

    def _xml_processing(
        self,
        xml_file_path: Path,
        dataset_number: int,
    ) -> None:
        """Processing of a XML file.

        Args:
            xml_file_path (Path): Path of the XML file.
            dataset_number (int): The number of the dataset (Between 1 and 4).
        """

        try:
            # Load XML
            tree = self.xml_extractor.read(file_path=xml_file_path)
            self.statistics.xml_loaded += 1

            # Store rax XML (MinIO)
            xml_uri = self.minio_storage.put_xml(
                bucket_name=MINIO_SETTINGS.bucket_raw,
                file_name=f"{IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS.dataset_name}_{dataset_number}/{xml_file_path.stem}/annotation.xml",
                tree=tree,
            )

            if xml_uri is None:
                self.logger.error(
                    f"Failed to upload XML file to MinIO: {xml_file_path}"
                )
                raise

            self.statistics.xml_uploaded += 1

            # Extract metadata and annotations
            xml_metadata, annotations = self.xml_extractor.extract(
                tree=tree,
                title=xml_file_path.stem,
                dataset_name=f"{IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS.dataset_name}_{dataset_number}",
            )
            xml_metadata = self.xml_extractor.enrich_with_directory_name(
                xml_metadata=xml_metadata, xml_file_path=xml_file_path
            )

            # Upsert recording (PostgreSQL)
            recording = self.postgres_storage.select_recording(
                dataset_name=xml_metadata.dataset_name, title=xml_metadata.title
            )

            if recording is None:
                recording = self.postgres_storage.insert_recording(
                    dataset_name=xml_metadata.dataset_name,
                    title=xml_metadata.title,
                )
                if recording is None:
                    self.logger.error(
                        f"Failed to insert recording to PostgreSQL: {xml_file_path}"
                    )
                    raise
                self.statistics.recordings_inserted += 1

            else:
                recording = self.postgres_storage.update_recording(
                    id_recording=recording["id_recording"],
                    dataset_name=xml_metadata.dataset_name,
                    title=xml_metadata.title,
                )
                if recording is None:
                    self.logger.error(
                        f"Failed to update recording to PostgreSQL: {xml_file_path}"
                    )
                    raise
                self.statistics.recordings_updated += 1

            id_recording = recording["id_recording"]

            # Upsert annotation_file (PostgreSQL)
            annotation_file = self.postgres_storage.select_annotation_file(
                id_recording=id_recording, annotation_type=AnnotationType.XML
            )

            if annotation_file is None:
                result = self.postgres_storage.insert_annotation_file(
                    id_recording=id_recording,
                    annotation_type=AnnotationType.XML,
                    uri=xml_uri,
                )
                if result is None:
                    self.logger.error(
                        f"Failed to insert annotation_file to PostgreSQL: {xml_file_path}"
                    )
                    raise
                self.statistics.annotation_file_inserted += 1

            else:
                result = self.postgres_storage.update_annotation_file(
                    id_annotation=annotation_file["id_annotation"],
                    annotation_type=AnnotationType.XML,
                    uri=xml_uri,
                )
                if result is None:
                    self.logger.error(
                        f"Failed to update annotation_file to PostgreSQL: {xml_file_path}"
                    )
                    raise
                self.statistics.annotation_file_updated += 1

            # Upsert idmt_smt_guitar_metadata (PostgreSQL)
            idmt_smt_guitar_metadata = (
                self.postgres_storage.select_idmt_smt_guitar_metadata(
                    id_recording=id_recording
                )
            )

            if idmt_smt_guitar_metadata is None:
                result = self.postgres_storage.insert_idmt_smt_guitar_metadata(
                    id_recording=id_recording,
                    metadata=xml_metadata,
                )
                if result is None:
                    self.logger.error(
                        f"Failed to insert idmt_smt_guitar_metadata to PostgreSQL: {xml_file_path}"
                    )
                    raise
                self.statistics.idmt_smt_guitar_metadata_inserted += 1

            else:
                result = self.postgres_storage.update_idmt_smt_guitar_metadata(
                    id_recording=id_recording,
                    metadata=xml_metadata,
                )
                if result is None:
                    self.logger.error(
                        f"Failed to update idmt_smt_guitar_metadata to PostgreSQL: {xml_file_path}"
                    )
                    raise
                self.statistics.idmt_smt_guitar_metadata_updated += 1

            # Insert annotation_midi (Mongo)
            dict_annotation = annotations.to_dict()

            result = self.mongo_storage.insert_note_midi(note_midi=dict_annotation)
            if result == "inserted":
                self.statistics.xml_annotation_inserted += 1
            elif result == "updated":
                self.statistics.xml_annotation_updated += 1
            else:
                self.logger.error(
                    f"Failed to insert annotation to MongoDB: {xml_file_path}"
                )
                raise

        except Exception as exception:
            self.statistics.xml_error += 1
            self.logger.error(f"XML processing has failed: {exception}")

    def _xml_ingestion(
        self,
        directory_xml_path: Path,
        dataset_number: int,
    ) -> None:
        """Ingestion of XML files.

        Args:
            directory_xml_path (Path): Path of directory containing XML files.
            dataset_number (int): The number of the dataset (Between 1 and 4).
        """
        self.logger.debug("XML Ingestion...")

        if not directory_xml_path.exists():
            raise FileNotFoundError(
                f"Directory does not exist: path={directory_xml_path}"
            )

        xml_paths = list(directory_xml_path.glob("*.xml"))
        if self.ingestion_limit is not None:
            xml_paths = xml_paths[: self.ingestion_limit]

        nb_ingestion = 0
        for xml_file_path in tqdm(
            xml_paths,
            desc="XML ingestion",
            colour="green",
        ):
            self._xml_processing(
                xml_file_path=xml_file_path,
                dataset_number=dataset_number,
            )
            nb_ingestion += 1

        self.logger.debug(
            "XML Ingestion completed successfully: nb_ingestion={nb_ingestion}"
        )

    def _wav_processing(self, wav_file_path: Path, dataset_number: int) -> None:
        """Processing of a WAV file.

        Args:
            wav_file_path (Path): Path of the WAV file.
            dataset_number (int): The number of the dataset (Between 1 and 4).
        """

        try:
            # Load audio
            audio_data, sample_rate = self.wav_extractor.extract(
                file_path=wav_file_path
            )
            self.statistics.wav_loaded += 1

            # Make dataset_name and title
            dataset_name = f"{IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS.dataset_name}_{dataset_number}"
            title = wav_file_path.stem

            # Fetch recording (PostgreSQL)
            recording = self.postgres_storage.select_recording(
                dataset_name=dataset_name,
                title=title,
            )

            if recording is None:
                self.logger.error(f"Recording not found for WAV file: {wav_file_path}")
                raise

            id_recording = recording["id_recording"]

            # Store audio (MinIO)
            audio_uri = self.minio_storage.put_audio(
                bucket_name=MINIO_SETTINGS.bucket_raw,
                file_name=f"{dataset_name}/{title}/audio.wav",
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
            audio_type = AudioType.WAV

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

    def _wav_ingestion(self, directory_wav_path: Path, dataset_number: int) -> None:
        """Ingestion of XML files.

        Args:
            directory_wav_path (Path): Path of directory containing WAV files.
            dataset_number (int): The number of the dataset (Between 1 and 4).
        """

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
            self._wav_processing(
                wav_file_path=wav_file_path, dataset_number=dataset_number
            )
            nb_ingestion += 1

    def _add_pickup_prefix_to_filenames(self, directory_path: Path) -> None:
        """Add SC/HU prefix to filenames to avoid naming collisions.

        Args:
            directory_path (Path): Path of directories. Names of directories must be
            "Fender Strat Clean Neck SC Chords" or "Ibanez Power Strat Clean Bridge HU Chords".
        """

        try:
            supported_directory_names = [
                "Fender Strat Clean Neck SC Chords",
                "Ibanez Power Strat Clean Bridge HU Chords",
            ]

            if directory_path.name not in supported_directory_names:
                raise ValueError(
                    f"Unsupported directory: directory_name={directory_path.name}"
                )

            self.logger.info("Add SC/HU prefix to filenames...")

            modified_files_count = 0
            for subfolder, glob_pattern in {
                "annotation": "*.xml",
                "audio": "*.wav",
            }.items():
                subdirectory_path = directory_path / subfolder

                for file_path in subdirectory_path.glob(glob_pattern):
                    if not file_path.name.startswith(("SC", "HU")):
                        prefix = "SC" if " SC " in directory_path.name else "HU"
                        target_path = file_path.parent / f"{prefix}_{file_path.name}"
                        if not target_path.exists():
                            file_path.rename(target_path)
                            self.logger.debug(f"File renamed: {target_path}")
                            modified_files_count += 1
                        else:
                            self.logger.debug(
                                f"Target file already exists: {target_path}"
                            )

            self.logger.info(
                f"Adding SC/HU prefix to filenames completed, "
                f"modified_files_count={modified_files_count}"
            )
        except Exception as exception:
            self.logger.error(
                f"Adding SC/HU prefix to filenames has failed: {exception}"
            )
            raise

    def _dataset1_ingestion(self) -> None:
        """Ingestion of the dataset number 1."""

        if not IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS.dataset1_path.exists():
            raise FileNotFoundError(
                f"Directory does not exist: path={IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS.dataset1_path}"
            )

        paths = IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS.dataset1_path.glob("*")
        dir_paths = [p for p in paths if p.is_dir()]

        for dir_path in dir_paths:
            if "Chords" in dir_path.as_posix():
                self._add_pickup_prefix_to_filenames(directory_path=dir_path)

            self.logger.info(f"\tdirectory_name={dir_path.name}")
            self._xml_ingestion(
                directory_xml_path=dir_path / "annotation",
                dataset_number=1,
            )
            self._wav_ingestion(
                directory_wav_path=dir_path / "audio",
                dataset_number=1,
            )

    def _rename_audio_files_to_match_xml(self, dataset_path: Path) -> None:
        """Rename audio files to match annotation files.

        Args:
            dataset_path (Path): Path of dataset. Directory name must be "dataset2".
        """

        try:
            if dataset_path.name != "dataset2":
                raise ValueError(
                    f"Unsupported directory: directory_name={dataset_path.name}"
                )

            audio_dir = dataset_path / "audio"
            filename_mapping = {
                "AR_Lick11_FN.wav": "AR_Lick11_FNVSBHD.wav",
                "AR_Lick11_KN.wav": "AR_Lick11_KNVSBHD.wav",
                "AR_Lick11_MN.wav": "AR_Lick11_MNVSBHD.wav",
                "FS_Lick11_FN.wav": "FS_Lick11_FNVSBHD.wav",
                "FS_Lick11_KN.wav": "FS_Lick11_KNVSBHD.wav",
                "FS_Lick11_MN.wav": "FS_Lick11_MNVSBHD.wav",
                "LP_Lick11_FN.wav": "LP_Lick11_FNVSBHD.wav",
                "LP_Lick11_KN.wav": "LP_Lick11_KNVSBHD.wav",
                "LP_Lick11_MN.wav": "LP_Lick11_MNVSBHD.wav",
            }

            self.logger.info("Rename audio files to match annotation files...")

            modified_files_count = 0
            for old_file_name, new_file_name in filename_mapping.items():
                old_path = audio_dir / old_file_name
                new_path = old_path.parent / new_file_name

                if new_path.exists():
                    self.logger.debug(f"Already renamed: {new_path}")
                    continue

                if not old_path.exists():
                    raise FileNotFoundError(f"Missing file: {old_path}")

                old_path.rename(new_path)

                self.logger.debug(f"File renamed: {new_path}")
                modified_files_count += 1

            self.logger.info(
                f"Renaming audio files completed, modified_files_count={modified_files_count}"
            )
        except Exception as exception:
            self.logger.error(f"Renaming audio files has failed: {exception}")
            raise

    def _dataset_ingestion(self, dataset_path: Path, dataset_number: int) -> None:
        """Ingestion of a dataset.

        Args:
            dataset_path (Path): Path of dataset.
            dataset_number (int): The number of the dataset (2 or 3).
        """

        if not dataset_path.exists():
            raise FileNotFoundError(f"Directory does not exist: path={dataset_path}")

        if dataset_path.name == "dataset2":
            self._rename_audio_files_to_match_xml(dataset_path=dataset_path)

        self._xml_ingestion(
            directory_xml_path=dataset_path / "annotation",
            dataset_number=dataset_number,
        )
        self._wav_ingestion(
            directory_wav_path=dataset_path / "audio",
            dataset_number=dataset_number,
        )

    # TODO
    def _dataset4_ingestion(self) -> None:
        """Ingestion of the dataset number 4."""

        if not IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS.dataset4_path.exists():
            raise FileNotFoundError(
                f"Directory does not exist: path={IDMT_SMT_GUITAR_INGESTION_PIPELINE_SETTINGS.dataset1_path}"
            )

        self.logger.warning("dataset4 ingestion not implemented")
        return

        # chords_paths = Path(
        #     "C:/Users/Administrateur/Documents/projet_cdsd_data/idmt-smt-guitar/dataset4"
        # ).rglob("chords/*.csv")

        # patterns_paths = Path(
        #     "C:/Users/Administrateur/Documents/projet_cdsd_data/idmt-smt-guitar/dataset4"
        # ).rglob("patterns/*.txt")

        # onsets_paths = Path(
        #     "C:/Users/Administrateur/Documents/projet_cdsd_data/idmt-smt-guitar/dataset4"
        # ).rglob("onsets/*.csv")

        # texture_paths = Path(
        #     "C:/Users/Administrateur/Documents/projet_cdsd_data/idmt-smt-guitar/dataset4"
        # ).rglob("texture/*.txt")

        # audio_paths = Path(
        #     "C:/Users/Administrateur/Documents/projet_cdsd_data/idmt-smt-guitar/dataset4"
        # ).rglob("audio/*.wav")
