import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class PipelineType(StrEnum):
    DOWNLOADER = "downloader"
    INGESTOR = "ingestor"
    PREPROCESSOR = "preprocessor"
    DATASET_BUILDER = "dataset_builder"
    TRAINER = "trainer"
    EVALUATOR = "evaluator"
    PREDICTOR = "predictor"


@dataclass
class AbstractPipelineSettings(ABC):
    pipeline_name: str
    pipeline_type: PipelineType
    pipeline_version: str = "1.0.0"

    @abstractmethod
    def _to_metadata_dict(self) -> dict[str, Any]:
        return {}

    def to_mongo_dict(self) -> dict[str, Any]:
        mongo_dict = {
            "pipeline_name": self.pipeline_name,
            "pipeline_type": self.pipeline_type,
            "pipeline_version": self.pipeline_version,
            "metadata": self._to_metadata_dict(),
        }

        mongo_dict["_id"] = self._get_functional_key(mongo_dict)

        return mongo_dict

    def _get_functional_key(self, metadata) -> str:
        canonical = json.dumps(
            metadata,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        )

        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
