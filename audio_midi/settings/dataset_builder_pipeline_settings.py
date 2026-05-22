from dataclasses import dataclass, field
from typing import Any

from .abstract_pipeline_settings import AbstractPipelineSettings, PipelineType


@dataclass
class DatasetBuilderPipelineSettings(AbstractPipelineSettings):
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

    pipeline_name: str = "dataset_builder"
    pipeline_type: PipelineType = PipelineType.DATASET_BUILDER
    pipeline_version: str = "1.0.0"

    dataset_name: str = "context_window_small"

    use_guitarset: bool = True
    use_idmt_smt_guitar: bool = False
    max_samples_per_datasets: int | None = 100

    preprocessing_pipeline_id: str | None = (
        "587d316097f01069c08c4a855cfa3d3ac043c3f975bd689ac60e0d4affefbe65"
    )

    train_size: float = 0.7
    validation_size: float = 0.1
    test_size: float = 0.2
    random_state: int = 42
    shuffle: bool = True

    prefix_features: tuple[str] = ("cqt_",)
    prefix_target: tuple[str] = ("pitch_",)

    use_context_window: bool = True
    context_size: int = 11

    train_objects_names: list[str] = field(default_factory=list)
    train_samples: int = 0
    validation_objects_names: list[str] = field(default_factory=list)
    validation_samples: int = 0
    test_objects_names: list[str] = field(default_factory=list)
    test_samples: int = 0

    def _to_metadata_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "datasets_used": {
                "use_guitarset": self.use_guitarset,
                "use_idmt_smt_guitar": self.use_idmt_smt_guitar,
            },
            "max_samples_per_datasets": self.max_samples_per_datasets,
            "preprocessing_pipeline_id": self.preprocessing_pipeline_id,
            "split_train_test_validation": {
                "train_size": self.train_size,
                "val_size": self.validation_size,
                "test_size": self.test_size,
                "random_state": self.random_state,
                "shuffle": self.shuffle,
            },
            "split_features_target": {
                "prefix_features": self.prefix_features,
                "prefix_target": self.prefix_target,
            },
            "context_window": {
                "use_context_window": self.use_context_window,
                "context_size": self.context_size,
            },
            "datasets_objects_names": {
                "train_objects_names": self.train_objects_names,
                "train_samples": self.train_samples,
                "validation_objects_names": self.validation_objects_names,
                "validation_samples": self.validation_samples,
                "test_objects_names": self.test_objects_names,
                "test_samples": self.test_samples,
            },
        }


dataset_builder_pipeline_config = DatasetBuilderPipelineSettings()
