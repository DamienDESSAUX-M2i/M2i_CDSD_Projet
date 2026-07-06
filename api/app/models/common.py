from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from app.core import TIME_ZONE
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ResponseStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response."""

    model_config = ConfigDict(
        extra="forbid",
    )

    success: ResponseStatus = ResponseStatus.SUCCESS
    timestamp: datetime = Field(default_factory=datetime.now(TIME_ZONE))
    data: T


class InferenceMetrics(BaseModel):
    """Inference timing metrics."""

    model_config = ConfigDict(
        extra="forbid",
    )

    preprocessing_ms: float
    inference_ms: float
    postprocessing_ms: float
    total_ms: float


class ModelInfo(BaseModel):
    """Information about the loaded model."""

    model_config = ConfigDict(
        extra="forbid",
    )

    name: str
    framework: str = "tensorflow"
    version: str
    threshold: float
