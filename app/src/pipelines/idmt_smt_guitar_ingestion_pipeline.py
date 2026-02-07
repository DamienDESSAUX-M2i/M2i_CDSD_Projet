from dataclasses import dataclass
from pathlib import Path

from config import (
    idmt_smt_guitar_ingestion_pipeline_config,
    minio_config,
)
from tqdm import tqdm

from src.extractors import WAVExtractor, XMLExtractor
from src.pipelines import AbstractPipeline


@dataclass
class IDMTSMTGuitarIngestionPipelineStatistics:
    xml_loaded: int = 0
    xml_uploaded: int = 0
    xml_metadata_inserted: int = 0
    xml_metadata_updated: int = 0
    xml_annotation_inserted: int = 0
    xml_annotation_updated: int = 0
    xml_error: int = 0
    wav_loaded: int = 0
    wav_uploaded: int = 0
    wav_error: int = 0

    def to_dict(self) -> dict:
        """Cast the dataclass to a dictionary whose
        keys are attributes of the dataclass and
        values are values of the attributes."""
        return self.__dict__

    def to_string(self) -> str:
        """Create a string containing values of all attributes."""
        strs = [f"{k}={v}" for k, v in self.__dict__.items()]
        return ", ".join(strs)


class IDMTSMTGuitarIngestionPipeline(AbstractPipeline):
    """Ingestion Pipeline."""

    def __init__(self, ingestion_limit: int | None = None):
        super().__init__()
        self.xml_extractor = XMLExtractor()
        self.wav_extractor = WAVExtractor()
        self.ingestion_limit = (
            ingestion_limit or idmt_smt_guitar_ingestion_pipeline_config.ingestion_limit
        )
        self.statistics = IDMTSMTGuitarIngestionPipelineStatistics()

    def run(self):
        """Run pipeline.

        Raises:
            RuntimeError: If pipeline failed.
        """
        try:
            self.logger.info("IDMT SMT Guitar ingestion pipeline start...")

            self.logger.info("[1/4] Dataset1 ingestion")
            self._dataset1_ingestion()

            self.logger.info("[2/4] Dataset2 ingestion")
            self._dataset_ingestion(
                dataset_path=idmt_smt_guitar_ingestion_pipeline_config.dataset2_path,
                dataset_number=2,
            )

            self.logger.info("[3/4] Dataset3 ingestion")
            self._dataset_ingestion(
                dataset_path=idmt_smt_guitar_ingestion_pipeline_config.dataset2_path,
                dataset_number=3,
            )

            self.logger.info("[4/4] Dataset4 ingestion")
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
            tree = self.xml_extractor.read(file_path=xml_file_path)
            self.statistics.xml_loaded += 1

            self.minio_storage.put_xml(
                bucket_name=minio_config.bucket_raw,
                file_name=f"{idmt_smt_guitar_ingestion_pipeline_config.dataset_name}_{dataset_number}/{xml_file_path.stem}/annotation.xml",
                tree=tree,
            )
            self.statistics.xml_uploaded += 1

            xml_metadata = self.xml_extractor.extract_metadata(
                tree=tree,
                dataset_name=f"IDMT_SMT_Guitar_{dataset_number}",
            )
            xml_metadata = self.xml_extractor.enrich_with_directory_name(
                xml_metadata=xml_metadata, xml_file_path=xml_file_path
            )
            id_metadata = self.postgres_storage.select_metadata_title(
                title=xml_metadata.title
            )
            if id_metadata:
                result = self.postgres_storage.update_metadata(
                    id_metadata=id_metadata, metadata=xml_metadata
                )
                if result:
                    self.statistics.xml_metadata_updated += 1
                else:
                    self.statistics.xml_error += 1
            else:
                result = self.postgres_storage.insert_into_metadata(
                    metadata=xml_metadata
                )
                if result:
                    self.statistics.xml_metadata_inserted += 1
                else:
                    self.statistics.xml_error += 1

            annotations = self.xml_extractor.extract_annotation(
                tree=tree, dataset_name="IDMT_SMT_Guitar_1"
            )
            dict_annotation = annotations.to_dict()

            result = self.mongo_storage.insert_note_midi(note_midi=dict_annotation)
            self.statistics.xml_annotation_inserted += 1 if result == "inserted" else 0
            self.statistics.xml_annotation_updated += 1 if result == "updated" else 0
            self.statistics.xml_error += 1 if result == "errors" else 0

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
            audio_data, sample_rate = self.wav_extractor.extract(
                file_path=wav_file_path
            )
            self.statistics.wav_loaded += 1

            result = self.minio_storage.put_audio(
                bucket_name=minio_config.bucket_raw,
                file_name=f"{idmt_smt_guitar_ingestion_pipeline_config.dataset_name}_{dataset_number}/{wav_file_path.stem}/audio.wav",
                audio_data=audio_data,
                sample_rate=sample_rate,
            )
            if result:
                self.statistics.wav_uploaded += 1
            else:
                self.statistics.wav_error += 1

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

    def _dataset1_ingestion(self) -> None:
        """Ingestion of the dataset number 1."""
        if not idmt_smt_guitar_ingestion_pipeline_config.dataset1_path.exists():
            raise FileNotFoundError(
                f"Directory does not exist: path={idmt_smt_guitar_ingestion_pipeline_config.dataset1_path}"
            )

        paths = idmt_smt_guitar_ingestion_pipeline_config.dataset1_path.glob("*")
        dir_paths = [p for p in paths if p.is_dir()]

        for dir_path in dir_paths:
            self.logger.info(f"\tdirectory_name={dir_path.name}")
            self._xml_ingestion(
                directory_xml_path=dir_path / "annotation",
                dataset_number=1,
            )
            self._wav_ingestion(
                directory_wav_path=dir_path / "audio",
                dataset_number=1,
            )

    def _dataset_ingestion(self, dataset_path: Path, dataset_number: int) -> None:
        """Ingestion of a dataset.

        Args:
            dataset_path (Path): Path of dataset.
            dataset_number (int): The number of the dataset (Between 1 and 4).
        """
        if not dataset_path.exists():
            raise FileNotFoundError(f"Directory does not exist: path={dataset_path}")

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
        if not idmt_smt_guitar_ingestion_pipeline_config.dataset4_path.exists():
            raise FileNotFoundError(
                f"Directory does not exist: path={idmt_smt_guitar_ingestion_pipeline_config.dataset1_path}"
            )

        chords_paths = Path(
            "C:/Users/Administrateur/Documents/projet_cdsd_data/idmt-smt-guitar/dataset4"
        ).rglob("chords/*.csv")

        patterns_paths = Path(
            "C:/Users/Administrateur/Documents/projet_cdsd_data/idmt-smt-guitar/dataset4"
        ).rglob("patterns/*.txt")

        onsets_paths = Path(
            "C:/Users/Administrateur/Documents/projet_cdsd_data/idmt-smt-guitar/dataset4"
        ).rglob("onsets/*.csv")

        texture_paths = Path(
            "C:/Users/Administrateur/Documents/projet_cdsd_data/idmt-smt-guitar/dataset4"
        ).rglob("texture/*.txt")

        audio_paths = Path(
            "C:/Users/Administrateur/Documents/projet_cdsd_data/idmt-smt-guitar/dataset4"
        ).rglob("audio/*.wav")
