import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from settings import (
    DATASET_BUILDER_PIPELINE_SETTINGS,
    MONGO_SETTINGS,
)
from settings.abstract_pipeline_settings import PipelineType
from sklearn.model_selection import train_test_split

from src.pipelines import AbstractPipeline
from src.transformers import PrefixFeaturesTarget
from src.utils import Statistics

PREFIX_FEATURES: tuple[str] = (
    PrefixFeaturesTarget.STFT.value,
    PrefixFeaturesTarget.MEL_SPECTROGRAM.value,
    PrefixFeaturesTarget.CQT.value,
    PrefixFeaturesTarget.CQT_CHROMAGRAM.value,
    PrefixFeaturesTarget.MFCC.value,
)

PREFIX_TARGET: tuple[str] = (PrefixFeaturesTarget.TARGET.value,)


@dataclass
class DatasetBuilderPipelineStatistics(Statistics):
    """
    Runtime statistics tracker for the dataset builder pipeline.

    This class aggregates counters and metadata about dataset construction
    operations including loading, splitting, and persistence.

    Attributes:
        pipeline_metadata_inserted: Whether pipeline metadata was inserted into MongoDB.
        pipeline_metadata_updated: Whether pipeline metadata was updated in MongoDB.
        dataset_builder_error: Number of failed dataset loading or processing operations.
        sample_metadata_loaded: Number of sample metadata entries loaded from MongoDB.
        dataset_metadata_inserted: Whether dataset metadata was inserted into MongoDB.
        dataset_metadata_updated: Whether dataset metadata was updated in MongoDB.
        sample_loaded: Number of successfully loaded samples from MinIO.
        dataset_load: Number of dataset loading phase completed successfully. Expected 3.
        dataset_size: Total number of frames across train/validation/test splits.
        train_size: Number of training samples.
        validation_size: Number of validation samples.
        test_size: Number of test samples.
        train_ratio: Percentage of training samples in full dataset.
        validation_ratio: Percentage of validation samples in full dataset.
        test_ratio: Percentage of test samples in full dataset.
    """

    # Pipeline metrics
    pipeline_metadata_inserted: bool = False
    pipeline_metadata_updated: bool = False

    # Dataset metrics
    dataset_builder_error: int = 0
    sample_metadata_loaded: int = 0
    dataset_metadata_inserted: bool = False
    dataset_metadata_updated: bool = False
    sample_loaded: int = 0
    dataset_load: int = 0
    dataset_size: int = 0
    train_size: int = 0
    train_ratio: int = 0
    validation_size: int = 0
    validation_ratio: int = 0
    test_size: int = 0
    test_ratio: int = 0


class DatasetBuilderPipeline(AbstractPipeline):
    """
    Dataset builder pipeline responsible for constructing a machine learning
    dataset from preprocessed samples stored in MinIO.

    The pipeline performs the following steps:

        1. Load sample metadata from MongoDB.
        2. Split metadata into train/validation/test sets.
        3. Load feature/target tensors from MinIO (Parquet files).
        4. Optionally build temporal context windows.
        5. Aggregate datasets into final ML-ready structures.
        6. Persist dataset and pipeline metadata into MongoDB.

    Expected data format:

        Each sample stored in MinIO must be a Parquet file containing:
            - feature columns prefixed by PREFIX_FEATURES
            - target columns prefixed by PREFIX_TARGET

    Notes:
        - The pipeline is frame-level (time-aligned data).
        - It assumes preprocessing has already been applied.
        - It is deterministic given a fixed preprocessing_pipeline_id.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """
        Initialize the dataset builder pipeline.

        Args:
            logger:
                Logger instance used for structured logging.

        Side Effects:
            - Loads dataset builder configuration from settings.
            - Resolves preprocessing_pipeline_id if not provided.
            - Prepares MongoDB metadata structure.
            - Initializes internal DataFrame storage.
            - Initializes runtime statistics tracker.

        Raises:
            RuntimeError:
                If no valid preprocessing pipeline can be resolved.
        """

        super().__init__(logger)
        self.settings = DATASET_BUILDER_PIPELINE_SETTINGS

        if self.settings.preprocessing_pipeline_id is None:
            self._get_latest_preprocessing_pipeline_id()
        self.pipeline_metadata = self.settings.to_mongo_dict()

        self.df_metadata: pd.DataFrame | None = None
        self.df_train_metadata: pd.DataFrame | None = None
        self.df_validation_metadata: pd.DataFrame | None = None
        self.df_test_metadata: pd.DataFrame | None = None

        self.statistics = DatasetBuilderPipelineStatistics()

    def _get_latest_preprocessing_pipeline_id(self) -> None:
        """
        Resolve the most recent preprocessing pipeline identifier from MongoDB.

        This method queries the pipeline metadata collection and retrieves
        the latest pipeline of type PREPROCESSOR.

        Returns:
            None

        Side Effects:
            - Updates self.settings.preprocessing_pipeline_id

        Raises:
            RuntimeError:
                If no preprocessing pipeline metadata exists in database.
        """

        self.logger.info("Getting latest preprocessing pipeline id")

        pipeline = [
            {
                "$match": {"pipeline_type": PipelineType.PREPROCESSOR.value},
            },
            {
                "$sort": {
                    "inserted_at": -1,
                }
            },
            {
                "$limit": 1,
            },
            {
                "$project": {
                    "_id": 1,
                }
            },
        ]

        documents = self.mongo_storage.aggregate_documents(
            collection_name=MONGO_SETTINGS.collection_pipeline_metadata,
            pipeline=pipeline,
        )

        if not documents:
            raise RuntimeError("No preprocessing pipeline fetch")

        self.settings.preprocessing_pipeline_id = documents[0]["_id"]

        self.logger.info(
            f"Preprocessing pipeline fetch: preprocessing_pipeline_id={self.settings.preprocessing_pipeline_id}"
        )

    def _load_sample_metadata(self) -> None:
        """
        Load sample metadata associated with the selected preprocessing pipeline.

        This method queries MongoDB for all samples matching:
            - preprocessing_pipeline_id
            - dataset_name in configured datasets_used

        Returns:
            None

        Side Effects:
            - Populates self.df_metadata with a pandas DataFrame
            - Updates statistics.sample_metadata_loaded

        Raises:
            ValueError:
                If no metadata entries are found.
        """

        self.logger.info(
            f"Loading sample metadata for preprocessing_pipeline_id={self.settings.preprocessing_pipeline_id}"
        )

        pipeline = [
            {
                "$match": {
                    "preprocessing_pipeline_id": self.settings.preprocessing_pipeline_id,
                    "dataset_name": {"$in": list(self.settings.datasets_used)},
                }
            }
        ]

        documents = self.mongo_storage.aggregate_documents(
            collection_name=MONGO_SETTINGS.collection_sample_metadata,
            pipeline=pipeline,
        )

        self.df_metadata = pd.DataFrame(documents)

        if self.df_metadata.empty:
            raise ValueError(
                "No sample metadata found: "
                f"preprocessing_pipeline_id={self.settings.preprocessing_pipeline_id}"
            )

        self.statistics.sample_metadata_loaded += len(self.df_metadata)
        self.logger.info(f"Loaded {len(self.df_metadata)} sample metadata entries.")

    def _split_train_validation_test(self) -> None:
        """
        Split dataset metadata into train, validation, and test subsets.

        The split is deterministic and based on sklearn.train_test_split.

        Strategy:
            1. Split full dataset into train + test
            2. Split train subset into train + validation

        Returns:
            None

        Side Effects:
            - Populates:
                - self.df_train_metadata
                - self.df_validation_metadata
                - self.df_test_metadata

        Raises:
            ValueError:
                If metadata has not been loaded before splitting.
        """

        if self.df_metadata is None:
            raise ValueError("Metadata must be loaded before splitting.")

        self.logger.info("Starting train / validation / test split.")

        df_train_metadata, self.df_test_metadata = train_test_split(
            self.df_metadata,
            test_size=self.settings.test_size,
            random_state=self.settings.random_state,
            shuffle=self.settings.shuffle,
        )

        self.df_train_metadata, self.df_validation_metadata = train_test_split(
            df_train_metadata,
            test_size=self.settings.validation_size,
            random_state=self.settings.random_state,
            shuffle=self.settings.shuffle,
        )

        self.logger.info(
            "Dataset metadata split completed: "
            f"dataset={len(self.df_metadata)}, "
            f"train={len(self.df_train_metadata)}, "
            f"val={len(self.df_validation_metadata)}, "
            f"test={len(self.df_test_metadata)}"
        )

    def _save_pipeline_metadata(self):
        """
        Persist pipeline metadata to MongoDB.

        This ensures reproducibility and traceability of dataset construction
        experiments.

        Returns:
            None

        Side Effects:
            - Inserts or updates pipeline metadata in MongoDB
            - Updates pipeline statistics flags

        Raises:
            RuntimeError:
                If MongoDB insertion or update fails.
        """

        result = self.mongo_storage.insert_pipeline_metadata(
            pipeline_metadata=self.pipeline_metadata
        )

        if result == "inserted":
            self.logger.info("Pipeline metadata successfully inserted to MongoDB")
            self.statistics.pipeline_metadata_inserted += 1
        elif result == "updated":
            self.logger.info("Pipeline metadata successfully updated to MongoDB")
            self.statistics.pipeline_metadata_updated += 1
        else:
            raise RuntimeError(
                "Failed to insert pipeline metadata to MongoDB: "
                f"pipeline_type={self.pipeline_metadata['pipeline_type']}, _id={self.pipeline_metadata['_id']}"
            )

    def _save_dataset_metadata(self):
        """
        Persist dataset split metadata to MongoDB.

        Stored information includes:
            - train/validation/test object names
            - number of samples per split
            - linkage to dataset builder pipeline ID

        Returns:
            None

        Side Effects:
            - Inserts or updates dataset metadata in MongoDB
            - Updates dataset statistics flags

        Raises:
            RuntimeError:
                If MongoDB operation fails.
        """

        dataset_metadata = {
            "dataset_builder_pipeline_id": self.pipeline_metadata["_id"],
            "train_objects_names": self.df_train_metadata["object_name"].to_list(),
            "train_samples": len(self.df_train_metadata),
            "validation_objects_names": self.df_validation_metadata[
                "object_name"
            ].to_list(),
            "validation_samples": len(self.df_validation_metadata),
            "test_objects_names": self.df_test_metadata["object_name"].to_list(),
            "test_samples": len(self.df_test_metadata),
        }

        result = self.mongo_storage.insert_dataset_metadata(
            pipeline_metadata=dataset_metadata
        )

        if result == "inserted":
            self.logger.info("Dataset metadata successfully inserted to MongoDB")
            self.statistics.dataset_metadata_inserted += 1
        elif result == "updated":
            self.logger.info("Dataset metadata successfully updated to MongoDB")
            self.statistics.dataset_metadata_updated += 1
        else:
            raise RuntimeError(
                "Failed to insert dataset metadata to MongoDB: "
                f"pipeline_type={self.pipeline_metadata['pipeline_type']}, _id={self.pipeline_metadata['_id']}"
            )

    def _split_features_target(
        self,
        dataset: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split a sample dataframe into feature and target components.

        Args:
            dataset:
                Input dataframe containing both feature and target columns.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]:
                A tuple containing:
                    - features dataframe
                    - target dataframe

        Raises:
            ValueError:
                If no feature or target columns are found.
        """

        feature_columns = [
            column for column in dataset.columns if column.startswith(PREFIX_FEATURES)
        ]

        target_columns = [
            column for column in dataset.columns if column.startswith(PREFIX_TARGET)
        ]

        if not feature_columns:
            raise ValueError("No feature columns found.")

        if not target_columns:
            raise ValueError("No target columns found.")

        features = dataset[feature_columns]
        target = dataset[target_columns]

        return features, target

    def _load_dataset(
        self,
        df_metadata: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load full dataset split from MinIO based on metadata entries.

        Each entry in df_metadata must contain:
            - bucket_name
            - object_name

        Workflow:
            1. Load Parquet file from MinIO
            2. Split into features and targets
            3. Optionally build context windows
            4. Aggregate all samples

        Args:
            df_metadata:
                Metadata describing dataset samples.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]:
                - Concatenated feature matrix
                - Concatenated target matrix

        Raises:
            ValueError:
                If no valid samples could be loaded.
        """

        self.logger.info(f"Loading dataset from {len(df_metadata)} metadata entries.")

        samples: list[tuple[pd.DataFrame, pd.DataFrame]] = []

        for row in df_metadata.itertuples():
            sample = self.minio_storage.get_parquet(
                bucket_name=row.bucket_name,
                file_name=row.object_name,
            )

            if sample is None:
                self.statistics.dataset_builder_error += 1
                self.logger.error(
                    f"Failed loading sample: uri={row.bucket_name}/{row.object_name} "
                )
                continue

            self.statistics.sample_loaded += 1

            features, target = self._split_features_target(dataset=sample)
            if self.settings.use_context_window:
                features = self._build_context_windows(features=features)

            samples.append((features, target))

        if not samples:
            raise ValueError("No samples could be loaded.")

        features_concat = pd.concat(
            [features for features, _ in samples],
            axis=0,
            ignore_index=True,
        )

        targets_concat = pd.concat(
            [targets for _, targets in samples],
            axis=0,
            ignore_index=True,
        )

        self.statistics.dataset_load += 1
        self.logger.info(
            f"Dataset loaded: "
            f"features_shape={features_concat.shape}, "
            f"target_shape={targets_concat.shape}"
        )

        return features_concat, targets_concat

    def _build_context_windows(
        self,
        features: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Construct temporal context windows for frame-wise features.

        Each frame is expanded into a sliding window of neighboring frames,
        enabling temporal context for downstream ML models.

        Example:
            context_size = 2

            Input:
                f0, f1, f2, f3

            Output:
                [f0,f0,f0,f1,f2]
                [f0,f0,f1,f2,f3]
                [f0,f1,f2,f3,f3]
                [f1,f2,f3,f3,f3]

        Padding strategy:
            Edge padding (replication of boundary frames)

        Args:
            features:
                Input feature matrix of shape (n_frames, n_features)

        Returns:
            pd.DataFrame:
                Context-expanded feature matrix of shape:
                (n_frames, n_features * (2 * context_size + 1))

        Raises:
            ValueError:
                If input dataframe is empty.
        """

        self.logger.info(
            f"Building context windows: context_size={self.settings.context_size}"
        )

        if features.empty:
            raise ValueError("Input DataFrame is empty.")

        padding = self.settings.context_size
        window_size = 2 * padding + 1

        feature_columns = list(features.columns)

        features_array = features.to_numpy(dtype=np.float32)

        features_padded = np.pad(
            features_array,
            pad_width=((padding, padding), (0, 0)),
            mode="edge",
        )

        windows: list[np.ndarray] = []

        for i in range(len(features)):
            window = features_padded[i : i + window_size]
            windows.append(window.reshape(-1))

        features_context_array = np.stack(windows)

        context_columns = []

        for offset in range(-padding, padding + 1):
            for column in feature_columns:
                context_columns.append(f"{column}_t{offset:+d}")

        features_context = pd.DataFrame(
            data=features_context_array,
            columns=context_columns,
            index=features.index,
        )

        self.logger.info(
            f"Context windows built: "
            f"input={features.shape}, "
            f"output={features_context.shape}"
        )

        return features_context

    def _compute_stats(self, train, validation, test):
        """
        Compute and store dataset split statistics for the pipeline run.

        This method aggregates the sizes of the train, validation, and test
        datasets and computes both absolute counts and relative ratios.

        The results are stored in `self.statistics` and are intended for:
            - experiment tracking
            - reproducibility logging
            - dataset auditability

        Args:
            train (pd.DataFrame):
                Training dataset containing feature-target aligned samples.
            val (pd.DataFrame):
                Validation dataset containing feature-target aligned samples.
            test (pd.DataFrame):
                Test dataset containing feature-target aligned samples.

        Notes:
            - Ratios are computed as: split_size / total_dataset_size
            - This method assumes that all splits are non-empty.
            - No normalization or validation is performed here; inputs must already
              be validated by the pipeline execution logic.
        """

        total = len(train) + len(validation) + len(test)

        self.statistics.dataset_size = total

        self.statistics.train_size = len(train)
        self.statistics.train_ratio = len(train) / total

        self.statistics.validation_size = len(validation)
        self.statistics.validation_ratio = len(validation) / total

        self.statistics.test_size = len(test)
        self.statistics.test_ratio = len(test) / total

    def run(
        self,
    ) -> tuple[
        tuple[pd.DataFrame, pd.DataFrame],
        tuple[pd.DataFrame, pd.DataFrame],
        tuple[pd.DataFrame, pd.DataFrame],
    ]:
        """
        Execute the full dataset builder pipeline.

        Pipeline stages:

            1. Load sample metadata from MongoDB.
            2. Split metadata into train/validation/test sets.
            3. Load datasets from MinIO.
            4. Persist pipeline metadata.
            5. Persist dataset metadata.
            6. Compute final dataset statistics.

        Returns:
            tuple:
                (train_features, train_targets),
                (validation_features, validation_targets),
                (test_features, test_targets)

        Raises:
            RuntimeError:
                If any stage of the pipeline fails.
        """

        try:
            self.logger.info("Starting dataset builder pipeline.")

            self._load_sample_metadata()
            self._split_train_validation_test()
            train_dataset = self._load_dataset(df_metadata=self.df_train_metadata)
            validation_dataset = self._load_dataset(
                df_metadata=self.df_validation_metadata
            )
            test_dataset = self._load_dataset(df_metadata=self.df_test_metadata)
            self._save_pipeline_metadata()
            self._save_dataset_metadata()
            self._compute_stats(
                train=train_dataset, validation=validation_dataset, test=test_dataset
            )

            self.logger.info(
                "Dataset builder pipeline completed successfully: "
                f"train={len(train_dataset)}, "
                f"val={len(validation_dataset)}, "
                f"test={len(test_dataset)}"
            )

            return train_dataset, validation_dataset, test_dataset

        except Exception as exception:
            self.logger.error(f"ML pipeline failed: {exception}")
            raise RuntimeError("ML pipeline failed.") from exception
