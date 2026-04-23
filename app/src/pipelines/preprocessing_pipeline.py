from dataclasses import dataclass
from typing import Dict, Optional

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
from src.utils import Statistics


@dataclass
class PreprocessingPipelineStatistics(Statistics):
    audio_loaded: int = 0
    audio_normalized: int = 0
    audio_cleaned: int = 0
    audio_uploaded: int = 0
    audio_error: int = 0
    feature_extracted: int = 0
    feature_uploaded: int = 0
    feature_error: int = 0


class PreprocessingPipeline(AbstractPipeline):
    """
    End-to-end audio processing pipeline using MinIO storage.

    Workflow:
        raw (bronze) → processed (silver) → features (gold)

    Steps:
        1. Load raw audio from MinIO
        2. Normalize audio
        3. Clean audio
        4. Extract features
        5. Store cleaned audio in processed bucket
        6. Store features in output bucket
    """

    def __init__(
        self,
        guitarset: bool = True,
        idmt_smt_guitar: bool = True,
        preprocessing_limit: int | None = None,
    ) -> None:
        super().__init__()
        self.guitarset = guitarset
        self.idmt_smt_guitar = idmt_smt_guitar
        self.preprocessing_limit = (
            preprocessing_limit or preprocessing_pipeline_config.preprocessing_limit
        )
        self.normalizer = AudioNormalizer()
        self.cleaner = AudioCleaner()
        self.extractor = AudioFeatureExtractor()
        self.statistics = PreprocessingPipelineStatistics()

    def _load_audio(self, file_name: str) -> Optional[tuple[np.ndarray, int]]:
        """
        Load audio from MinIO raw bucket.
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
        Save cleaned audio to processed bucket.
        """
        self.logger.debug(
            f"Saving cleaned audio: uri={minio_config.bucket_processed}/{file_name}"
        )

        result = self.minio_storage.put_audio(
            bucket_name=minio_config.bucket_processed,
            file_name=file_name,
            audio_data=audio_data,
            sample_rate=sample_rate,
        )

        if result is None:
            self.statistics.audio_error += 1
        else:
            self.statistics.audio_uploaded += 1

    def _save_features(
        self,
        features: Dict[str, np.ndarray],
        file_name: str,
    ) -> list[str | None]:
        """
        Save each feature in a separate Parquet file.
        Each feature is stored independently in MinIO.
        """

        self.logger.debug(
            f"Saving features as separate Parquet files: uri={minio_config.bucket_raw}/{file_name}"
        )

        file_name_without_extension = ".".join(file_name.split(".")[:-1])

        for feature_name, matrix in features.items():
            try:
                self.logger.debug(
                    f"Saving feature: {file_name_without_extension}_{feature_name}"
                )

                if matrix.ndim == 2:
                    df = pd.DataFrame(matrix.T)
                else:
                    df = pd.DataFrame({feature_name: matrix})

                feature_file_name = (
                    f"{file_name_without_extension}_{feature_name}.parquet"
                )

                result = self.minio_storage.put_parquet(
                    bucket_name=minio_config.bucket_processed,
                    file_name=feature_file_name,
                    dataframe=df,
                )

                if result is None:
                    self.statistics.feature_error += 1
                else:
                    self.statistics.feature_uploaded += 1

            except Exception as e:
                self.logger.error(
                    f"Failed to save feature {file_name_without_extension}_{feature_name}: {e}",
                    exc_info=True,
                )

        self.logger.debug("Feature saving completed.")

    def _process_audio(self, file_name: str) -> None:
        """
        Process a single audio file.
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

            features = self.extractor.extract_features(
                audio_data,
                sample_rate,
                use_stft=preprocessing_pipeline_config.use_stft,
                use_mel=preprocessing_pipeline_config.use_mel,
                use_cqt=preprocessing_pipeline_config.use_cqt,
                use_chroma=preprocessing_pipeline_config.use_chroma,
                use_mfcc=preprocessing_pipeline_config.use_mfcc,
            )
            self.statistics.feature_extracted += len(features)

            self._save_clean_audio(audio_data, sample_rate, file_name)

            self._save_features(features, file_name)

            self.logger.debug(f"Processing completed: {file_name}")

        except Exception as e:
            self.logger.error(f"Error processing {file_name}: {e}", exc_info=True)

    def _process_guitar_set(self):
        self.logger.debug("GuitarSet preprocessing...")

        files_names = [
            obj.object_name
            for obj in self.minio_storage.list_raw(prefix="GuitarSet/")
            if "audio" in obj.object_name
        ]

        if self.preprocessing_limit is not None:
            files_names = files_names[
                : self.preprocessing_limit * 4
            ]  # 4 audio files per title

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
        pass

    def run(self):
        """Run pipeline.

        Raises:
            RuntimeError: If pipeline failed.
        """
        try:
            self.logger.info("Preprocessing pipeline stars")

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
