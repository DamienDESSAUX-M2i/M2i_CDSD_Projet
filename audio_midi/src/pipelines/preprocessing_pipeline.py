import logging
from dataclasses import dataclass

import pandas as pd
from settings import (
    GUITAR_SET_SETTINGS,
    IDMT_SMT_GUITAR_SETTINGS,
    MINIO_SETTINGS,
    PREPROCESSING_PIPELINE_SETTINGS,
)
from tqdm import tqdm

from src.models import AudioType
from src.pipelines import AbstractPipeline
from src.transformers import (
    AudioCleaner,
    AudioFeatureExtractor,
    AudioNormalizer,
)
from src.transformers.piano_roll_builder import (
    MIDIPitchMapper,
    PianoRollBuilder,
    TimeMapper,
)
from src.utils import FloatAudioArray, Statistics


@dataclass
class PreprocessingPipelineStatistics(Statistics):
    """
    Statistics tracker for the preprocessing pipeline.

    Attributes:
        pipeline_metadata_inserted: Pipeline metadata insertion status into MongoDB.
        pipeline_metadata_inserted: Pipeline metadata updating status in MongoDB.
        audio_loaded: Number of successfully loaded raw audio files.
        audio_normalized: Number of successfully normalized audio files.
        audio_cleaned: Number of successfully cleaned audio files.
        audio_uploaded: Number of cleaned audio files uploaded to MinIO.
        annotation_file_inserted: Number of new annotation file rows inserted into PostgreSQL.
        annotation_file_updated: Number of existing annotation file rows updated in PostgreSQL.
        audio_error: Number of audio processing or upload failures.
        feature_extracted: Number of successful feature extraction operations.
        piano_roll_builded: Number of successfully generated piano-roll targets.
        sample_uploaded: Number of final samples successfully uploaded.
        sample_error: Number of sample saving failures.
        sample_metadata_inserted: Number of sample metadata inserted into MongoDB.
        sample_metadata_updated: Number of sample metadata updated in MongoDB.
    """

    # Pipeline metric
    pipeline_metadata_inserted: bool = False
    pipeline_metadata_updated: bool = False

    # Audio metrics
    audio_error: int = 0
    audio_loaded: int = 0
    audio_normalized: int = 0
    audio_cleaned: int = 0
    audio_uploaded: int = 0
    feature_extracted: int = 0
    piano_roll_builded: int = 0
    audio_file_inserted: int = 0
    audio_file_updated: int = 0

    # Sample metrics
    sample_error: int = 0
    sample_uploaded: int = 0
    sample_metadata_inserted: int = 0
    sample_metadata_updated: int = 0


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
        logger: logging.Logger,
        guitarset: bool = True,
        idmt_smt_guitar: bool = True,
        dataset1: bool = True,
        dataset2: bool = True,
        dataset3: bool = True,
        dataset4: bool = True,
        preprocessing_limit: int | None = None,
    ) -> None:
        """
        Initialize the preprocessing pipeline.

        Args:
            logger (logging.Logger): Logger instance.
            guitarset: Whether to process GuitarSet dataset.
            idmt_smt_guitar: Whether to process IDMT-SMT-Guitar dataset.
            preprocessing_limit: Optional limit on the number of files to process.
                If None, the default value from configuration is used.
        """

        super().__init__(logger)
        self.settings = PREPROCESSING_PIPELINE_SETTINGS
        self.pipeline_metadata = self.settings.to_mongo_dict()

        self.guitarset = guitarset
        self.idmt_smt_guitar = idmt_smt_guitar
        self.dataset1 = dataset1
        self.dataset2 = dataset2
        self.dataset3 = dataset3
        self.dataset4 = dataset4
        self.preprocessing_limit = (
            preprocessing_limit or self.settings.preprocessing_limit
        )

        self.normalizer = AudioNormalizer(logger=logger)
        self.cleaner = AudioCleaner(
            logger=logger,
            n_fft=self.settings.n_fft,
            hop_length=self.settings.hop_length,
        )
        self.extractor = AudioFeatureExtractor(
            logger=logger,
            n_fft=self.settings.n_fft,
            hop_length=self.settings.hop_length,
            n_mels=self.settings.n_mels,
            n_mfcc=self.settings.n_mfcc,
            n_cqt_bins=self.settings.n_cqt_bins,
            bins_per_octave=self.settings.bins_per_octave,
            cqt_fmin=self.settings.cqt_fmin,
            chroma_cqt_norm=self.settings.chroma_cqt_norm,
        )
        self.piano_roll_builder = PianoRollBuilder(
            logger=logger,
            pitch_mapper=MIDIPitchMapper(
                midi_pitch_min=self.settings.midi_pitch_min,
                midi_pitch_max=self.settings.midi_pitch_max,
            ),
            time_mapper=TimeMapper(
                sample_rate=self.settings.target_sample_rate,
                hop_length=self.settings.hop_length,
            ),
        )

        self.statistics = PreprocessingPipelineStatistics()

    def _load_audio(self, file_name: str) -> tuple[FloatAudioArray, int] | None:
        """
        Load an audio file from the MinIO raw bucket.

        Args:
            file_name: Object path of the audio file inside the raw bucket.

        Returns:
            A tuple containing:
                - audio_data: Audio waveform as a NumPy array of shape (n_samples,) or (n_channels, n_samples)
                - sample_rate: Sampling rate in Hz

            Returns None if loading fails.
        """

        self.logger.debug(f"Loading audio: uri={MINIO_SETTINGS.bucket_raw}/{file_name}")

        result = self.minio_storage.get_audio(
            bucket_name=MINIO_SETTINGS.bucket_raw,
            file_name=file_name,
        )

        if result is None:
            self.logger.error(
                f"Failed to load audio: uri={MINIO_SETTINGS.bucket_raw}/{file_name}"
            )
            self.statistics.audio_error += 1
            return None

        self.statistics.audio_loaded += 1

        # Adapt soundfile shape to librosa shape
        audio_data, sample_rate = result
        if audio_data.ndim == 2:
            audio_data = audio_data.T

        return audio_data, sample_rate

    def _save_clean_audio(
        self,
        audio_data: FloatAudioArray,
        sample_rate: int,
        file_name: str,
    ) -> None:
        """
        Save cleaned audio to the MinIO processed bucket.

        The output filename is automatically generated using the original file path
        and the current pipeline execution metadata identifier.

        Args:
            audio_data: Cleaned audio waveform, a NumPy array of shape (n_samples,) or (n_channels, n_samples).
            sample_rate: Sampling rate in Hz.
            file_name: Original raw audio file path used to derive output path.
        """

        self.logger.debug(f"Saving cleaned audio: file_name={file_name}")

        try:
            # Extract dataset_name and title
            file_name_split = file_name.split("/")
            dataset_name = file_name_split[0]
            title = file_name_split[1]

            # Fetch recording (PostgreSQL)
            recording = self.postgres_storage.select_recording(
                dataset_name=dataset_name, title=title
            )

            if recording is None:
                self.logger.error(
                    f"Recording not found for WAV file: "
                    f"dataset_name={dataset_name}, title={title}"
                )
                raise

            id_recording = recording["id_recording"]

            # Store audio (MinIO)
            file_name_cleaned_audio = f"{'/'.join(file_name.split('/')[:-1])}/{self.pipeline_metadata['_id']}/audio_cleaned.wav"

            # Adapt librosa shape to soundfile shape
            if audio_data.ndim == 2:
                audio_data = audio_data.T

            audio_uri = self.minio_storage.put_audio(
                bucket_name=MINIO_SETTINGS.bucket_processed,
                file_name=file_name_cleaned_audio,
                audio_data=audio_data,
                sample_rate=sample_rate,
            )

            if audio_uri is None:
                self.logger.error(
                    "Failed to upload WAV file to MinIO: "
                    f"dataset_name={dataset_name}, title={title}"
                )
                raise

            self.statistics.audio_uploaded += 1

            # Upsert audio_file (PostgreSQL)
            audio_type = AudioType.PROCESSED_AUDIO

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
                        "Failed to insert audio_file to PostgreSQL: "
                        f"dataset_name={dataset_name}, title={title}"
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
                        "Failed to insert audio_file to PostgreSQL: "
                        f"dataset_name={dataset_name}, title={title}"
                    )
                    raise
                self.statistics.audio_file_updated += 1

        except Exception as exception:
            self.statistics.audio_error += 1
            self.logger.error(f"WAV processing has failed: {exception}")

    def _save_sample(
        self,
        sample: pd.DataFrame,
        file_name: str,
    ) -> None:
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
        """

        self.logger.debug(
            f"Saving samples as separate Parquet files: file_name={file_name}"
        )

        try:
            bucket_name = MINIO_SETTINGS.bucket_processed
            sample_file_name = f"{'/'.join(file_name.split('/')[:-1])}/{self.pipeline_metadata['_id']}/sample.parquet"

            uri = f"{bucket_name}/{sample_file_name}"
            self.logger.debug(f"Saving samples: uri={uri}")

            result = self.minio_storage.put_parquet(
                bucket_name=bucket_name,
                file_name=sample_file_name,
                dataframe=sample,
            )

            if result is None:
                self.logger.error(f"Failed to upload WAV file to MinIO: uri={uri}")
                raise

            self.statistics.sample_uploaded += 1

            file_name_split = file_name.split("/")
            dataset_name = file_name_split[0]
            title = file_name_split[1]

            sample_metadata = {
                "preprocessing_pipeline_id": self.pipeline_metadata["_id"],
                "dataset_name": dataset_name,
                "title": title,
                "bucket_name": bucket_name,
                "object_name": sample_file_name,
                "n_frames": sample.shape[0],
            }
            result = self.mongo_storage.insert_sample_metadata(
                sample_metadata=sample_metadata
            )

            if result == "inserted":
                self.statistics.sample_metadata_inserted += 1
            elif result == "updated":
                self.statistics.sample_metadata_updated += 1
            else:
                self.logger.error(
                    "Failed to insert sample metadata to MongoDB: "
                    f"bucket_name={bucket_name}, object_name={sample_file_name}"
                )
                raise

        except Exception as exception:
            self.statistics.sample_error += 1
            self.logger.error(
                f"Failed to save samples: "
                f"uri={MINIO_SETTINGS.bucket_processed}/{sample_file_name}, "
                f"error={exception}"
            )

        self.logger.debug("Sample saving completed.")

    def _process_sample(self, file_name: str, df_annotations: pd.DataFrame) -> None:
        """
        Process a single audio file end-to-end.

        Steps:
            1. Load raw audio
            2. Convert to mono
            3. Remove DC offset
            4. Resample
            5. Clean signal
            6. Normalize signal
            7. Cast to float32
            8. Optionally save cleaned audio
            9. Extract features
            10. Build piano-roll labels
            11. Merge features and labels
            12. Optionally save final sample

        Args:
            file_name: Object path of the audio file inside the raw bucket.
        """
        try:
            result = self._load_audio(file_name=file_name)
            if result is None:
                return

            audio_data, sample_rate = result

            # Convert to mono
            audio_data = self.normalizer.to_mono(audio_data=audio_data)

            # Remove DC offset
            if self.settings.use_remove_dc_offset:
                audio_data = self.normalizer.remove_dc_offset(audio_data=audio_data)

            # Resample
            audio_data, sample_rate = self.normalizer.resample(
                audio_data=audio_data,
                sample_rate=sample_rate,
                target_sample_rate=self.settings.target_sample_rate,
            )

            # Clean Audio
            audio_data = self.cleaner.clean(
                audio_data,
                sample_rate,
                use_highpass=self.settings.use_highpass,
                highpass_cutoff=self.settings.highpass_cutoff,
                use_lowpass=self.settings.use_lowpass,
                lowpass_cutoff=self.settings.lowpass_cutoff,
                denoise_method=self.settings.denoise_method,
                wiener_strength=self.settings.wiener_strength,
                use_trim=self.settings.use_trim,
                trim_db=self.settings.trim_db,
            )
            self.statistics.audio_cleaned += 1

            # Normalize
            audio_data = self.normalizer.normalize(
                audio_data=audio_data,
                normalization_type=self.settings.normalization_type,
                target_peak=self.settings.target_peak,
                target_rms=self.settings.target_rms,
            )

            # Cast to float32
            if self.settings.use_to_float32:
                audio_data = self.normalizer.to_float32(audio_data=audio_data)

            self.statistics.audio_normalized += 1

            # Save cleaned audio
            if self.settings.save_clean_audio:
                self._save_clean_audio(audio_data, sample_rate, file_name)

            # Extract Features
            features = self.extractor.extract(
                audio_data,
                sample_rate,
                use_stft=self.settings.use_stft,
                use_mel=self.settings.use_mel,
                use_cqt=self.settings.use_cqt,
                use_chroma=self.settings.use_chroma,
                use_mfcc=self.settings.use_mfcc,
            )

            self.statistics.feature_extracted += 1

            # Build Piano Roll
            n_frames = features.shape[0]
            piano_roll = self.piano_roll_builder.transform(
                df_annotations=df_annotations,
                n_frames=n_frames,
            )

            self.statistics.piano_roll_builded += 1

            # Build sample frame-wise
            sample = pd.concat([features, piano_roll], axis=1)

            # Save sample
            if self.settings.save_sample:
                self._save_sample(sample, file_name)

            self.logger.debug(f"Processing completed: {file_name}")

        except Exception as e:
            self.logger.error(f"Error processing {file_name}: {e}", exc_info=True)

    def _load_guitar_set_annotations(self) -> pd.DataFrame:
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

        Returns:
            A pandas DataFrame containing flattened note annotations with columns :
                - title
                - onset
                - duration
                - midi_pitch
        """

        pipeline = [{"$match": {"dataset_name": GUITAR_SET_SETTINGS.name}}]

        annotations = self.mongo_storage.aggregate_documents(
            collection_name="note_midi", pipeline=pipeline
        )

        if len(annotations) == 0:
            return pd.DataFrame()

        df_annotations = pd.DataFrame(annotations)[["title", "note_midi"]]

        df_annotations = df_annotations.explode("note_midi").reset_index(drop=True)
        df_annotations = df_annotations.join(
            pd.json_normalize(df_annotations["note_midi"])
        )
        df_annotations = df_annotations.rename(
            columns={"time": "onset", "value": "midi_pitch"}
        )

        df_annotations["onset"] = df_annotations["onset"].astype(float)
        df_annotations["duration"] = df_annotations["duration"].astype(float)
        df_annotations["midi_pitch"] = df_annotations["midi_pitch"].round().astype(int)

        return df_annotations[["title", "onset", "duration", "midi_pitch"]]

    def _load_idmt_smt_guitar_annotations(self, dataset_number: str) -> pd.DataFrame:
        """
        Load note-level annotations from MongoDB and convert them into a flat DataFrame.

        Expected annotation format:
            {
                "onset": float,
                "offset": float,
                "pitch": int
            }

        The nested note_midi structure is exploded and normalized into a tabular format
        suitable for piano-roll construction.

        Args:
            dataset_number: Number of the dataset. Must be between 1 and 4.

        Returns:
            A pandas DataFrame containing flattened note annotations with columns :
                - title
                - onset
                - duration
                - midi_pitch
        """

        pipeline = [
            {
                "$match": {
                    "dataset_name": f"{IDMT_SMT_GUITAR_SETTINGS.name}_{dataset_number}"
                }
            }
        ]

        annotations = self.mongo_storage.aggregate_documents(
            collection_name="note_midi", pipeline=pipeline
        )

        if len(annotations) == 0:
            return pd.DataFrame()

        df_annotations = pd.DataFrame(annotations)[["title", "transcription"]]

        df_annotations = df_annotations.explode("transcription").reset_index(drop=True)
        df_annotations = df_annotations.join(
            pd.json_normalize(df_annotations["transcription"])
        )
        df_annotations["duration"] = df_annotations["offset"] - df_annotations["onset"]
        df_annotations = df_annotations.rename(columns={"pitch": "midi_pitch"})

        df_annotations["onset"] = df_annotations["onset"].astype(float)
        df_annotations["duration"] = df_annotations["duration"].astype(float)
        df_annotations["midi_pitch"] = df_annotations["midi_pitch"].round().astype(int)

        return df_annotations[["title", "onset", "duration", "midi_pitch"]]

    def _process_guitar_set(self):
        """
        Run preprocessing for the GuitarSet dataset.

        This method:
            - lists GuitarSet audio files from MinIO raw bucket
            - filters the selected audio source
            - optionally limits the number of processed files
            - processes each audio file individually

        Only the selected audio source `audio_hex-pickup_mix` is currently used.
        """

        self.logger.info("GuitarSet preprocessing...")

        files_names = [
            obj.object_name
            for obj in self.minio_storage.list_raw(
                prefix=f"{GUITAR_SET_SETTINGS.name}/"
            )
            if AudioType.AUDIO_MONO_PICKUP_MIX.value in obj.object_name
        ]

        if self.preprocessing_limit is not None:
            files_names = files_names[: self.preprocessing_limit]

        df_annotations = self._load_guitar_set_annotations()
        if df_annotations.empty:
            self.logger.warning("No annotations loaded, skip preprocessing")
            return

        nb_ingestion = 0
        for file_name in tqdm(
            files_names,
            desc="GuitarSet preprocessing",
            colour="green",
        ):
            self._process_sample(
                file_name=file_name,
                df_annotations=df_annotations[
                    df_annotations["title"] == file_name.split("/")[1]
                ],
            )
            nb_ingestion += 1

        self.logger.debug(
            f"GuitarSet preprocessing completed: nb_ingestion={nb_ingestion}"
        )

    def _process_idmt_smt_guitar(self, dataset_number: int):
        """
        Run preprocessing for the IDMT-SMT-Guitar dataset.

        This method:
            - lists IDMT-SMT-Guitar audio files from MinIO raw bucket
            - filters the selected audio source
            - optionally limits the number of processed files
            - processes each audio file individually

        Args:
            dataset_number (int): Number of the sub-dataset. Must be between 1 and 4.

        Only the selected audio source `audio_hex-pickup_mix` is currently used.
        """

        self.logger.info(f"IDMT-SMT-Guitar dataset{dataset_number} preprocessing...")

        files_names = [
            obj.object_name
            for obj in self.minio_storage.list_raw(
                prefix=f"{IDMT_SMT_GUITAR_SETTINGS.name}_{dataset_number}/"
            )
            if "audio.wav" in obj.object_name
        ]

        if self.preprocessing_limit is not None:
            files_names = files_names[: self.preprocessing_limit]

        df_annotations = self._load_idmt_smt_guitar_annotations(
            dataset_number=dataset_number
        )
        if df_annotations.empty:
            self.logger.warning("No annotations loaded, skip preprocessing")
            return

        nb_ingestion = 0
        for file_name in tqdm(
            files_names,
            desc=f"IDMT-SMT-Guitar dataset{dataset_number} preprocessing",
            colour="green",
        ):
            self._process_sample(
                file_name=file_name,
                df_annotations=df_annotations[
                    df_annotations["title"] == file_name.split("/")[1]
                ],
            )
            nb_ingestion += 1

        self.logger.debug(
            f"GuitarSet preprocessing completed: nb_ingestion={nb_ingestion}"
        )

    def _insert_pipeline_metadata(self) -> None:
        """
        Save pipeline execution metadata into MongoDB.

        This metadata stores:
            - preprocessing parameters
            - execution identifier
            - reproducibility information

        It ensures experiment traceability across multiple preprocessing runs.
        """

        result = self.mongo_storage.insert_pipeline_metadata(
            pipeline_metadata=self.pipeline_metadata
        )

        if result == "inserted":
            self.statistics.pipeline_metadata_inserted = True
        elif result == "updated":
            self.statistics.pipeline_metadata_updated = True
        else:
            self.logger.error(
                "Failed to insert pipeline metadata to MongoDB: "
                f"_id={self.pipeline_metadata['_id']}"
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

            self._insert_pipeline_metadata()

            if self.guitarset:
                self._process_guitar_set()

            if self.idmt_smt_guitar:
                if self.dataset1:
                    self._process_idmt_smt_guitar(dataset_number=1)
                if self.dataset2:
                    self._process_idmt_smt_guitar(dataset_number=2)
                if self.dataset3:
                    self._process_idmt_smt_guitar(dataset_number=3)
                if self.dataset4:
                    self._process_idmt_smt_guitar(dataset_number=4)

            self.logger.info(
                f"Preprocessing pipeline ends successfully: {self.statistics.to_string()}"
            )
            self.close()
        except Exception as exc:
            self.logger.error("Preprocessing pipeline failed.")
            raise RuntimeError("Preprocessing pipeline failed") from exc
