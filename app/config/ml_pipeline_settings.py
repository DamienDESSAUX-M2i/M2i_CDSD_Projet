import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MLPipelineSettings:
    """
    Configuration settings for the ML pipeline.

    This configuration centralizes all parameters required for:
        - loading preprocessed samples
        - selecting a preprocessing pipeline version
        - train / validation / test split strategy
        - dataset loading strategy
        - future model training and evaluation settings

    The configuration can also be serialized and stored in MongoDB
    to ensure experiment reproducibility and traceability.
    """

    pipeline_name: str = "ml"
    pipeline_version: str = "1.0.0"

    random_state: int = 42

    preprocessing_pipeline_id: str = (
        "587d316097f01069c08c4a855cfa3d3ac043c3f975bd689ac60e0d4affefbe65"
    )

    train_size: float = 0.8
    val_size: float = 0.1
    test_size: float = 0.1
    shuffle: bool = True

    def to_mongo_dict(self) -> dict[str, Any]:
        """
        Convert settings into a MongoDB-compatible dictionary.

        This method is used to persist ML pipeline metadata in MongoDB
        for experiment tracking and reproducibility.

        Returns:
            dict[str, Any]:
                Dictionary representation of the configuration.
                Includes:
                    - pipeline_name
                    - created_at
                    - all dataclass fields
        """

        metadata = {
            "pipeline_name": self.pipeline_name,
            "pipeline_version": self.pipeline_version,
            "metadata": {
                "random_state": self.random_state,
                "preprocessing_pipeline_id": self.preprocessing_pipeline_id,
                "split_train_test_validation": {
                    "train_size": self.train_size,
                    "val_size": self.val_size,
                    "test_size": self.test_size,
                    "shuffle": self.shuffle,
                },
            },
        }

        metadata["_id"] = self.get_functional_key(metadata)

        return metadata

    def get_functional_key(self, metadata) -> str:
        """
        Generates a stable functional key from a potentially nested dictionary.
        """
        canonical = json.dumps(
            metadata,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        )

        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


ml_pipeline_config = MLPipelineSettings()
