import pandas as pd
from config import ml_pipeline_config, mongo_config
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
        guitarset: bool = True,
        idmt_smt_guitar: bool = True,
    ) -> None:
        """
        Initialize the ML pipeline.

        Args:
            guitarset: Whether to process GuitarSet dataset.
            idmt_smt_guitar: Whether to process IDMT-SMT-Guitar dataset.
        """
        super().__init__()
        self.use_guitar_set = guitarset
        self.use_idmt_smt_guitar = idmt_smt_guitar

        self.pipeline_metadata = ml_pipeline_config.to_mongo_dict()
        self.preprocessing_pipeline_id = ml_pipeline_config.preprocessing_pipeline_id
        self.test_size = ml_pipeline_config.test_size
        self.val_size = ml_pipeline_config.val_size
        self.shuffle = ml_pipeline_config.shuffle
        self.random_state = ml_pipeline_config.random_state

        self.df_metadata: pd.DataFrame | None = None
        self.df_train_metadata: pd.DataFrame | None = None
        self.df_val_metadata: pd.DataFrame | None = None
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
            collection_name=mongo_config.collection_sample_metadata,
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

        self.df_train_metadata, self.df_val_metadata = train_test_split(
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
        self.pipeline_metadata["val_objects_names"] = self.df_val_metadata[
            "object_name"
        ].to_list()

        self.logger.info(
            "Dataset split completed: "
            f"dataset={len(self.df_metadata)}, "
            f"train={len(self.df_train_metadata)}, "
            f"val={len(self.df_val_metadata)}, "
            f"test={len(self.df_test_metadata)}"
        )

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
        val_dataset = self._load_dataset(df_metadata=self.df_val_metadata)
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
