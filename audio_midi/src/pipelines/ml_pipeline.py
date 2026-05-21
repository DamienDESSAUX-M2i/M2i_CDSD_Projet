import logging

import numpy as np
import pandas as pd
from settings import MONGO_SETTINGS, ml_pipeline_config
from sklearn.model_selection import train_test_split

from src.pipelines import AbstractPipeline


class MLPipeline(AbstractPipeline):
    """
    Machine Learning pipeline for dataset preparation.

    Responsibilities:
        1. Load sample metadata associated with a preprocessing pipeline
        2. Split samples into train / validation / test sets at title level
        3. Load train / validation / test datasets from MinIO

    Notes:
        - Split is performed title-wise to avoid data leakage
        - Each sample corresponds to one processed audio title
        - This class does not handle model training yet
    """

    def __init__(
        self,
        logger: logging.Logger,
        guitarset: bool = True,
        idmt_smt_guitar: bool = True,
    ) -> None:
        """
        Initialize the ML pipeline.

        Args:
            guitarset: Whether to process GuitarSet dataset.
            idmt_smt_guitar: Whether to process IDMT-SMT-Guitar dataset.
        """
        super().__init__(logger)
        self.use_guitar_set = guitarset
        self.use_idmt_smt_guitar = idmt_smt_guitar

        self.pipeline_metadata = ml_pipeline_config.to_mongo_dict()

        self.preprocessing_pipeline_id = ml_pipeline_config.preprocessing_pipeline_id

        self.test_size = ml_pipeline_config.test_size
        self.val_size = ml_pipeline_config.val_size
        self.random_state = ml_pipeline_config.random_state
        self.shuffle = ml_pipeline_config.shuffle

        self.use_context_window = ml_pipeline_config.use_context_window
        self.context_size = ml_pipeline_config.context_size

        self.df_metadata: pd.DataFrame | None = None
        self.df_train_metadata: pd.DataFrame | None = None
        self.df_validation_metadata: pd.DataFrame | None = None
        self.df_test_metadata: pd.DataFrame | None = None

    def _load_sample_metadata(self) -> pd.DataFrame:
        """
        Load sample metadata associated with a preprocessing pipeline.

        Returns:
            pd.DataFrame:
                DataFrame containing all samples metadata for the given
                preprocessing pipeline.

        Raises:
            ValueError:
                If no sample metadata is found.
        """
        self.logger.info(
            f"Loading sample metadata for preprocessing_pipeline_id={self.preprocessing_pipeline_id}"
        )

        pipeline = [
            {
                "$match": {
                    "preprocessing_pipeline_id": self.preprocessing_pipeline_id,
                }
            }
        ]

        documents = self.mongo_storage.aggregate_documents(
            collection_name=MONGO_SETTINGS.collection_sample_metadata,
            pipeline=pipeline,
        )

        df_metadata = pd.DataFrame(documents)

        if df_metadata.empty:
            raise ValueError(
                f"No sample metadata found for preprocessing_pipeline_id={self.preprocessing_pipeline_id}"
            )

        self.logger.info(f"Loaded {len(df_metadata)} sample metadata entries.")

        return df_metadata

    def _split_dataset(self) -> None:
        """
        Split dataset into train / validation / test sets using title-level split.

        Important:
            Split is performed on unique titles to avoid data leakage between
            train and test sets.

        Raises:
            ValueError:
                If metadata is not loaded.
        """
        if self.df_metadata is None:
            raise ValueError("Metadata must be loaded before splitting.")

        self.logger.info("Starting train / validation / test split.")

        df_train_metadata, self.df_test_metadata = train_test_split(
            self.df_metadata,
            test_size=self.test_size,
            random_state=self.random_state,
            shuffle=self.shuffle,
        )

        self.df_train_metadata, self.df_validation_metadata = train_test_split(
            df_train_metadata,
            test_size=self.val_size,
            random_state=self.random_state,
            shuffle=self.shuffle,
        )

        self.pipeline_metadata["train_objects_names"] = self.df_train_metadata[
            "object_name"
        ].to_list()
        self.pipeline_metadata["test_objects_names"] = self.df_test_metadata[
            "object_name"
        ].to_list()
        self.pipeline_metadata["validation_objects_names"] = (
            self.df_validation_metadata["object_name"].to_list()
        )

        self.logger.info(
            "Dataset split completed: "
            f"dataset={len(self.df_metadata)}, "
            f"train={len(self.df_train_metadata)}, "
            f"val={len(self.df_validation_metadata)}, "
            f"test={len(self.df_test_metadata)}"
        )

    def _split_features_target(
        self,
        dataset: pd.DataFrame,
        prefix_features: tuple[str] = ("cqt_",),
        prefix_target: tuple[str] = ("pitch_",),
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Extract features and targets from dataset.

        Args:
            dataset:
                Frame-wise dataset.

        Returns:
            tuple[np.ndarray, np.ndarray]:
                X:
                    Feature matrix of shape
                    (n_frames, n_features)

                y:
                    Piano-roll target matrix of shape
                    (n_frames, n_pitches)
        """
        feature_columns = [
            column for column in dataset.columns if column.startswith(prefix_features)
        ]

        target_columns = [
            column for column in dataset.columns if column.startswith(prefix_target)
        ]

        if not feature_columns:
            raise ValueError("No feature columns found.")

        if not target_columns:
            raise ValueError("No target columns found.")

        features = dataset[feature_columns]
        target = dataset[target_columns]

        return features, target

    def _build_context_windows(
        self,
        features: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Build centered temporal context windows from a frame-wise feature DataFrame.

        Example:
            context_size = 2

            input:
                frame_0
                frame_1
                frame_2
                frame_3

            output:
                [
                    [x0, x0, x0, x1, x2],
                    [x0, x0, x1, x2, x3],
                    [x0, x1, x2, x3, x3],
                    [x1, x2, x3, x3, x3],
                ]

        Padding strategy:
            Edge padding

        Args:
            X:
                Input feature DataFrame of shape
                (n_frames, n_features)

        Returns:
            pd.DataFrame:
                Context-window feature DataFrame of shape
                (
                    n_frames,
                    n_features * (2 * context_size + 1)
                )
        """
        self.logger.info(f"Building context windows: context_size={self.context_size}")

        if features.empty:
            raise ValueError("Input DataFrame is empty.")

        padding = self.context_size
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

    def _load_dataset(
        self,
        df_metadata: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Load dataset samples from MinIO using metadata.

        Args:
            df_metadata: Metadata DataFrame containing sample locations.

        Returns:
            pd.DataFrame:
                Concatenated dataset.

        Raises:
            ValueError:
                If no samples could be loaded.
        """
        self.logger.info(f"Loading dataset from {len(df_metadata)} metadata entries.")

        dataset = []

        for row in df_metadata.itertuples():
            try:
                sample_df = self.minio_storage.get_parquet(
                    bucket_name=row.bucket_name,
                    file_name=row.object_name,
                )

                if sample_df is not None:
                    if self.use_context_window:
                        features, target = self._split_features_target(
                            dataset=sample_df
                        )
                        features = self._build_context_windows(features=features)
                        dataset = pd.concat([features, target], axis=1)

                    dataset.append(sample_df)

            except Exception as exception:
                self.logger.error(
                    f"Failed loading sample: "
                    f"uri={row.bucket_name}/{row.object_name} "
                    f"error={exception}"
                )

        if not dataset:
            raise ValueError("No samples could be loaded.")

        dataset_df = pd.concat(
            dataset,
            axis=0,
            ignore_index=True,
        )

        self.logger.info(f"Loaded dataset with shape={dataset_df.shape}")

        return dataset_df

    def _upload_pipeline_metadata(self) -> None:
        """
        Save pipeline execution metadata into MongoDB.
        It ensures experiment traceability across multiple preprocessing runs.
        """

        result = self.mongo_storage.insert_pipeline_metadata(
            pipeline_metadata=self.pipeline_metadata
        )

    def _build_datasets(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Build train, validation, and test datasets from sample metadata.

        Workflow:
            1. Load sample metadata associated with the preprocessing pipeline
            2. Perform title-level dataset split
            3. Load train dataset from MinIO
            4. Load validation dataset from MinIO
            5. Load test dataset from MinIO

        This method is designed to externalize dataset construction so that
        datasets can be easily reused in notebooks for model exploration,
        prototyping, and experimentation without re-running the full pipeline.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
                A tuple containing:
                    - train_dataset
                    - val_dataset
                    - test_dataset

        Raises:
            ValueError:
                If no sample metadata is found or dataset loading fails.
        """
        self.logger.info("Building train / validation / test datasets.")

        self.df_metadata = self._load_sample_metadata()

        if self.df_metadata.empty:
            raise ValueError("No sample metadata found for the selected pipeline.")

        self.logger.info(f"Loaded {len(self.df_metadata)} sample metadata entries.")

        self._split_dataset()

        self.logger.info("Loading datasets from MinIO after metadata split.")

        train_dataset = self._load_dataset(df_metadata=self.df_train_metadata)
        val_dataset = self._load_dataset(df_metadata=self.df_validation_metadata)
        test_dataset = self._load_dataset(df_metadata=self.df_test_metadata)

        self.logger.info(
            "Datasets successfully built: "
            f"train_shape={train_dataset.shape}, "
            f"val_shape={val_dataset.shape}, "
            f"test_shape={test_dataset.shape}"
        )

        return train_dataset, val_dataset, test_dataset

    def run(self) -> None:
        """
        Execute the ML dataset preparation pipeline.

        Steps:
            1. Build train / validation / test datasets
            2. Upload ML pipeline metadata to MongoDB

        This method is intended for production execution of the ML pipeline,
        while `_build_datasets()` can be reused independently inside notebooks
        for experimentation and model exploration.

        Raises:
            RuntimeError:
                If the pipeline execution fails.
        """
        try:
            self.logger.info("Starting ML pipeline.")

            train_dataset, val_dataset, test_dataset = self._build_datasets()

            self._upload_pipeline_metadata()

            self.logger.info(
                "ML pipeline completed successfully: "
                f"train={len(train_dataset)}, "
                f"val={len(val_dataset)}, "
                f"test={len(test_dataset)}"
            )

        except Exception as exception:
            self.logger.error(
                f"ML pipeline failed: {exception}",
                exc_info=True,
            )
            raise RuntimeError("ML pipeline failed.") from exception
