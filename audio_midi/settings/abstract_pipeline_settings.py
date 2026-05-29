import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class PipelineType(StrEnum):
    """Enumeration of supported pipeline types."""

    DOWNLOADER = "downloader"
    INGESTOR = "ingestor"
    PREPROCESSOR = "preprocessor"
    DATASET_BUILDER = "dataset_builder"
    TRAINER = "trainer"
    EVALUATOR = "evaluator"
    PREDICTOR = "predictor"


@dataclass
class AbstractPipelineSettings(ABC):
    """Base configuration object for all pipeline settings.

    This class defines the common metadata shared across all pipeline
    components and provides deterministic serialization utilities for
    persistence and reproducibility.

    Attributes:
        pipeline_name: Human-readable pipeline identifier.
        pipeline_type: Category of the pipeline.
        pipeline_version: Semantic version of the pipeline definition.
    """

    pipeline_name: str
    pipeline_type: PipelineType
    pipeline_version: str = "1.0.0"

    @abstractmethod
    def _to_metadata_dict(self) -> dict[str, Any]:
        """Convert pipeline-specific settings into a metadata dictionary.

        Returns:
            A JSON-serializable dictionary containing pipeline-specific
            configuration values.
        """

        return {}

    def to_mongo_dict(self) -> dict[str, Any]:
        """Serialize settings into a MongoDB-compatible dictionary.

        The resulting dictionary contains a deterministic `_id` field
        computed from the canonicalized payload content.

        Returns:
            A MongoDB-compatible dictionary representation of the settings.
        """

        mongo_dict = {
            "pipeline_name": self.pipeline_name,
            "pipeline_type": self.pipeline_type.value,
            "pipeline_version": self.pipeline_version,
            "metadata": self._to_metadata_dict(),
        }

        mongo_dict["_id"] = self._get_functional_key(mongo_dict)

        return mongo_dict

    def _get_functional_key(self, metadata) -> str:
        """Generate a deterministic SHA-256 hash for a metadata payload.

        The payload is canonicalized using stable JSON serialization in
        order to ensure reproducible hashing across executions.

        Args:
            metadata: Metadata dictionary to hash.

        Returns:
            Hexadecimal SHA-256 digest string.
        """

        canonical = json.dumps(
            metadata,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        )

        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
