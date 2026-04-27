from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from config import minio_config, preprocessing_pipeline_config
from tqdm import tqdm

from src.pipelines import AbstractPipeline
from src.transformers import (
    AudioCleaner,
    AudioFeatureExtractor,
    AudioNormalizer,
)
from src.transformers.piano_roll_builder import (
    PianoRollBuilder,
    PitchMapper,
    TimeMapper,
)
from src.utils import Statistics


@dataclass
class PreprocessingPipelineStatistics(Statistics):
    """
    Statistics tracker for the preprocessing pipeline.

    Attributes:
        audio_loaded: Number of successfully loaded raw audio files.
        audio_normalized: Number of successfully normalized audio files.
        audio_cleaned: Number of successfully cleaned audio files.
        audio_uploaded: Number of cleaned audio files uploaded to MinIO.
        audio_error: Number of audio processing or upload failures.
        feature_extracted: Number of successful feature extraction operations.
        piano_roll_builded: Number of successfully generated piano-roll targets.
        sample_uploaded: Number of final samples successfully uploaded.
        sample_error: Number of sample saving failures.
    """

    audio_loaded: int = 0
    audio_normalized: int = 0
    audio_cleaned: int = 0
    audio_uploaded: int = 0
    audio_error: int = 0
    feature_extracted: int = 0
    piano_roll_builded: int = 0
    sample_uploaded: int = 0
    sample_error: int = 0


class PreprocessingPipeline(AbstractPipeline):
    """
    End-to-end preprocessing pipeline for automatic guitar transcription.

    This pipeline processes raw guitar audio files stored in MinIO and produces
    training-ready frame-based samples for supervised learning.

    Storage workflow:
        raw (bronze) -> processed (silver) -> output (gold)

    Main steps:
        1. Load raw audio from MinIO raw bucket
        2. Normalize audio signal
        3. Clean audio signal
        4. Optionally save cleaned audio
        5. Extract acoustic features
        6. Load note annotations from MongoDB
        7. Build aligned piano-roll targets
        8. Merge features and labels into a training sample
        9. Save final sample to MinIO processed bucket

    Supported datasets:
        - GuitarSet
        - IDMT-SMT-Guitar (planned)

    The final objective is to produce aligned frame-by-frame datasets for
    MIDI transcription model training.
    """

    def __init__(
        self,
        guitarset: bool = True,
        idmt_smt_guitar: bool = True,
        preprocessing_limit: int | None = None,
    ) -> None:
        """
        Initialize the preprocessing pipeline.

        Args:
            guitarset: Whether to process GuitarSet dataset.
            idmt_smt_guitar: Whether to process IDMT-SMT-Guitar dataset.
            preprocessing_limit: Optional limit on the number of files to process.
                If None, the default value from configuration is used.
        """

        super().__init__()
        self.guitarset = guitarset
        self.idmt_smt_guitar = idmt_smt_guitar
        self.preprocessing_limit = (
            preprocessing_limit or preprocessing_pipeline_config.preprocessing_limit
        )
        self.normalizer = AudioNormalizer()
        self.cleaner = AudioCleaner()
        self.extractor = AudioFeatureExtractor()
        self.piano_roll_builder = PianoRollBuilder(
            PitchMapper(
                midi_min=preprocessing_pipeline_config.midi_min,
                midi_max=preprocessing_pipeline_config.midi_max,
            ),
            TimeMapper(
                sample_rate=preprocessing_pipeline_config.target_sample_rate,
                hop_length=preprocessing_pipeline_config.hop_length,
            ),
        )
        self.statistics = PreprocessingPipelineStatistics()
        self.pipeline_metadata = preprocessing_pipeline_config.to_mongo_dict()

    def _load_audio(self, file_name: str) -> Optional[tuple[np.ndarray, int]]:
        """
        Load an audio file from the MinIO raw bucket.

        Args:
            file_name: Object path of the audio file inside the raw bucket.

        Returns:
            A tuple containing:
                - audio_data: Audio waveform as a NumPy array
                - sample_rate: Sampling rate in Hz

            Returns None if loading fails.
        """

        self.logger.debug(f"Loading audio: uri={minio_config.bucket_raw}/{file_name}")

        result = self.minio_storage.get_audio(
            bucket_name=minio_config.bucket_raw,
            file_name=file_name,
        )

        if result is None:
            self.logger.error(
                f"Failed to load audio: uri={minio_config.bucket_raw}/{file_name}"
            )
            self.statistics.audio_error += 1
            return None

        self.statistics.audio_loaded += 1
        return result

    def _save_clean_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        file_name: str,
    ) -> None:
        """
        Save cleaned audio to the MinIO processed bucket.

        The output filename is automatically generated using the original file path
        and the current pipeline execution metadata identifier.

        Args:
            audio_data: Cleaned audio waveform.
            sample_rate: Sampling rate in Hz.
            file_name: Original raw audio file path used to derive output path.
        """

        self.logger.debug(f"Saving cleaned audio: file_name={file_name}")

        file_name_audio_cleaned = f"{'/'.join(file_name.split('/')[:-1])}/audio_cleaned_{self.pipeline_metadata['_id']}.wav"

        result = self.minio_storage.put_audio(
            bucket_name=minio_config.bucket_processed,
            file_name=file_name_audio_cleaned,
            audio_data=audio_data,
            sample_rate=sample_rate,
        )

        if result is None:
            self.statistics.audio_error += 1
        else:
            self.statistics.audio_uploaded += 1

    def _save_sample(
        self,
        sample: pd.DataFrame,
        file_name: str,
    ) -> list[str | None]:
        """
        Save a processed training sample as a Parquet file.

        Each sample contains:
            - extracted features
            - aligned piano-roll target labels

        The sample is stored independently in the processed bucket to allow
        scalable dataset construction and downstream training workflows.

        Args:
            sample: Final sample DataFrame containing features and piano-roll labels.
            file_name: Original raw audio file path used to derive output path.

        Returns:
            A list containing upload result URIs or None values if saving fails.
        """

        self.logger.debug(
            f"Saving samples as separate Parquet files: file_name={file_name}"
        )

        try:
            sample_file_name = f"{'/'.join(file_name.split('/')[:-1])}/sample_{self.pipeline_metadata['_id']}.parquet"

            self.logger.debug(
                f"Saving samples: uri={minio_config.bucket_processed}/{sample_file_name}"
            )
            result = self.minio_storage.put_parquet(
                bucket_name=minio_config.bucket_processed,
                file_name=sample_file_name,
                dataframe=sample,
            )

            if result is None:
                self.statistics.sample_error += 1
            else:
                self.statistics.sample_uploaded += 1

        except Exception as e:
            self.logger.error(
                f"Failed to save samples: uri={minio_config.bucket_processed}/{sample_file_name}: {e}",
                exc_info=True,
            )

        self.logger.debug("Sample saving completed.")

    def _process_audio(self, file_name: str) -> None:
        """
        Process a single audio file end-to-end.

        Steps:
            1. Load raw audio
            2. Normalize waveform
            3. Clean signal
            4. Optionally save cleaned audio
            5. Extract selected features
            6. Load note annotations
            7. Build piano-roll labels
            8. Merge features and labels
            9. Optionally save final sample

        Args:
            file_name: Object path of the audio file inside the raw bucket.
        """
        try:
            result = self._load_audio(file_name=file_name)
            if result is None:
                return

            audio_data, sample_rate = result

            audio_data, sample_rate = self.normalizer.normalize(
                audio_data,
                sample_rate,
                norm_type=preprocessing_pipeline_config.norm_type,
            )
            self.statistics.audio_normalized += 1

            audio_data = self.cleaner.clean(
                audio_data,
                sample_rate,
                use_highpass=preprocessing_pipeline_config.use_highpass,
                highpass_cutoff=preprocessing_pipeline_config.highpass_cutoff,
                use_lowpass=preprocessing_pipeline_config.use_lowpass,
                lowpass_cutoff=preprocessing_pipeline_config.lowpass_cutoff,
                use_spectral_denoise=preprocessing_pipeline_config.use_spectral_denoise,
                use_wiener=preprocessing_pipeline_config.use_wiener,
                wiener_strength=preprocessing_pipeline_config.wiener_strength,
                use_trim=preprocessing_pipeline_config.use_trim,
                trim_db=preprocessing_pipeline_config.trim_db,
            )
            self.statistics.audio_cleaned += 1

            if preprocessing_pipeline_config.save_clean_audio:
                self._save_clean_audio(audio_data, sample_rate, file_name)

            features = self.extractor.extract_features(
                audio_data,
                sample_rate,
                use_stft=preprocessing_pipeline_config.use_stft,
                use_mel=preprocessing_pipeline_config.use_mel,
                use_cqt=preprocessing_pipeline_config.use_cqt,
                use_chroma=preprocessing_pipeline_config.use_chroma,
                use_mfcc=preprocessing_pipeline_config.use_mfcc,
            )
            self.statistics.feature_extracted += 1

            file_name_split = file_name.split("/")
            dataset_name = file_name_split[0]
            title = file_name_split[1]
            n_frames = features.shape[0]
            piano_roll = self.piano_roll_builder.transform(
                df_annotations=self._load_annotations(
                    dataset_name=dataset_name, title=title
                ),
                n_frames=n_frames,
            )
            self.statistics.piano_roll_builded += 1

            sample = pd.concat([features, piano_roll], axis=1)

            if preprocessing_pipeline_config.save_sample:
                self._save_sample(sample, file_name)

            self.logger.debug(f"Processing completed: {file_name}")

        except Exception as e:
            self.logger.error(f"Error processing {file_name}: {e}", exc_info=True)

    def _load_annotations(self, dataset_name: str, title: str) -> pd.DataFrame:
        """
        Load note-level annotations from MongoDB and convert them into a flat DataFrame.

        Expected annotation format:
            {
                "time": float,
                "duration": float,
                "value": int
            }

        The nested note_midi structure is exploded and normalized into a tabular format
        suitable for piano-roll construction.

        Args:
            dataset_name: Name of the source dataset (e.g. GuitarSet).
            title: Song title identifier.

        Returns:
            A pandas DataFrame containing flattened note annotations with columns such as:
                - time
                - duration
                - value
        """

        pipeline = [{"$match": {"dataset_name": dataset_name, "title": title}}]

        annotations = self.mongo_storage.aggregate_documents(
            collection_name="note_midi", pipeline=pipeline
        )
        df_annotations = pd.DataFrame(annotations)[["title", "note_midi"]]

        df_annotations = df_annotations.explode("note_midi").reset_index(drop=True)
        df_annotations = df_annotations.join(
            pd.json_normalize(df_annotations["note_midi"])
        )
        df_annotations = df_annotations.drop(
            columns=["title", "data_source", "note_midi"]
        )

        return df_annotations

    def _process_guitar_set(self):
        """
        Run preprocessing for the GuitarSet dataset.

        This method:
            - lists GuitarSet audio files from MinIO raw bucket
            - filters the selected audio source
            - optionally limits the number of processed files
            - processes each audio file individually

        Only the selected audio source
        (`audio_hex-pickup_debleeded`) is currently used.
        """

        self.logger.info("GuitarSet preprocessing...")

        files_names = [
            obj.object_name
            for obj in self.minio_storage.list_raw(prefix="GuitarSet/")
            if "audio_hex-pickup_debleeded" in obj.object_name
        ]

        if self.preprocessing_limit is not None:
            files_names = files_names[: self.preprocessing_limit]

        nb_ingestion = 0
        for file_name in tqdm(
            files_names,
            desc="GuitarSet audio preprocessing",
            colour="green",
        ):
            self._process_audio(file_name=file_name)
            nb_ingestion += 1

        self.logger.debug(
            f"GuitarSet preprocessing completed: nb_ingestion={nb_ingestion}"
        )

    # TODO
    def _process_idmt_smt_guitar(self):
        """
        Run preprocessing for the IDMT-SMT-Guitar dataset.

        This method is planned but not yet implemented.
        """

        pass

    def _upload_pipeline_metadata(self) -> None:
        """
        Save pipeline execution metadata into MongoDB.

        This metadata stores:
            - preprocessing parameters
            - execution identifier
            - reproducibility information

        It ensures experiment traceability across multiple preprocessing runs.
        """

        self.mongo_storage.insert_pipeline_metadata(
            pipeline_metadata=self.pipeline_metadata
        )

    def run(self):
        """
        Execute the full preprocessing pipeline.

        Workflow:
            1. Upload pipeline execution metadata
            2. Process GuitarSet if enabled
            3. Process IDMT-SMT-Guitar if enabled
            4. Log execution statistics
            5. Close storage connections properly

        Raises:
            RuntimeError: If the preprocessing pipeline fails.
        """

        try:
            self.logger.info("Preprocessing pipeline stars")

            self._upload_pipeline_metadata()

            if self.guitarset:
                self._process_guitar_set()

            if self.idmt_smt_guitar:
                self._process_idmt_smt_guitar()

            self.logger.info(
                f"Preprocessing pipeline ends successfully: {self.statistics.to_string()}"
            )
            self.close()
        except Exception as exc:
            self.logger.error("Preprocessing pipeline failed.")
            raise RuntimeError("Preprocessing pipeline failed") from exc
