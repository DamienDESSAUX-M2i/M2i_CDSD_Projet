import math
from dataclasses import dataclass
from typing import Any

from .abstract_pipeline_settings import AbstractPipelineSettings, PipelineType
from .datasets_settings import GUITAR_SET_SETTINGS


@dataclass
class DatasetBuilderPipelineSettings(AbstractPipelineSettings):
    """
    Configuration for dataset construction.

    This configuration controls:

    - Source datasets selection.
    - Preprocessing pipeline version selection.
    - Train / validation / test split strategy.
    - Context window generation.
    - Dataset reproducibility metadata.
    """

    pipeline_name: str = "dataset_builder_standard"
    pipeline_type: PipelineType = PipelineType.DATASET_BUILDER
    pipeline_version: str = "1.0.0"

    output_dataset_name: str = "guitar_set_standard"

    datasets_used: tuple[str, ...] = (GUITAR_SET_SETTINGS.name,)
    max_samples_per_dataset: int | None = 10

    preprocessing_pipeline_id: str | None = None

    train_size: float = 0.7
    validation_size: float = 0.1
    test_size: float = 0.2
    random_state: int = 73
    shuffle: bool = True

    use_context_window: bool = False
    context_size: int = 11

    def __post_init__(self) -> None:
        """Validate dataset builder configuration after initialization."""

        if not self.datasets_used:
            raise ValueError("datasets_used is empty")

        if not self.max_samples_per_dataset < 10:
            raise ValueError(
                "max_samples_per_dataset must be greater than or equals to 10"
            )

        for name, value in (
            ("train_size", self.train_size),
            ("validation_size", self.validation_size),
            ("test_size", self.test_size),
        ):
            if value < 0.0:
                raise ValueError(
                    f"{name} must be greater than or equals to 0.0 (got {value})"
                )

        total = self.train_size + self.validation_size + self.test_size
        if not math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("train_size + validation_size + test_size must equal 1.0")

        if self.random_state < 0:
            raise ValueError("random_state must be greater than or equals to 0")

        if self.use_context_window:
            if self.context_size < 1:
                raise ValueError("conxtext_size must be greater than or equals to 1")

            if self.context_size % 2 == 0:
                raise ValueError("context_size must be an odd number.")

    def _to_metadata_dict(self) -> dict[str, Any]:
        """
        Convert settings into a serializable metadata dictionary.

        The returned dictionary is used to:

        - Generate the functional pipeline identifier.
        - Persist pipeline settings in MongoDB.
        - Ensure dataset reproducibility and traceability.

        Returns:
            dict[str, Any]:
                Nested dictionary containing all dataset builder
                configuration parameters.
        """

        return {
            "dataset_name": self.output_dataset_name,
            "datasets_used": self.datasets_used,
            "max_samples_per_dataset": self.max_samples_per_dataset,
            "preprocessing_pipeline_id": self.preprocessing_pipeline_id,
            "dataset_split": {
                "train_size": self.train_size,
                "val_size": self.validation_size,
                "test_size": self.test_size,
                "random_state": self.random_state,
                "shuffle": self.shuffle,
            },
            "context_window": {
                "use_context_window": self.use_context_window,
                "context_size": self.context_size,
            },
        }


DATASET_BUILDER_PIPELINE_SETTINGS = DatasetBuilderPipelineSettings()
