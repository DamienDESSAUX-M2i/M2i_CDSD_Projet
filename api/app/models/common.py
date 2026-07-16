from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.core import TIME_ZONE

T = TypeVar("T")


class ResponseStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


def current_time() -> datetime:
    return datetime.now(TIME_ZONE)


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response."""

    model_config = ConfigDict(
        extra="forbid",
    )

    success: ResponseStatus = ResponseStatus.SUCCESS
    timestamp: datetime = Field(default_factory=current_time)
    data: T


class InferenceMetrics(BaseModel):
    """Inference timing metrics."""

    model_config = ConfigDict(
        extra="forbid",
    )

    preprocessing_secondes: float
    inference_secondes: float
    postprocessing_secondes: float
    total_secondes: float


class ModelInfo(BaseModel):
    """Information about the loaded model."""

    model_config = ConfigDict(
        extra="forbid",
    )

    name: str
    framework: str = "tensorflow"
    version: str
    input_shape: tuple[int, ...]
    output_shape: tuple[int, ...]
    threshold: float
