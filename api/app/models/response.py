from typing import Literal

from pydantic import BaseModel, ConfigDict

from .common import HealthStatus, InferenceMetrics, ModelInfo


class HealthResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    status: HealthStatus
    model_loaded: bool
    tensorflow_version: str
    python_version: str
    device: Literal["gpu", "cpu"]


class PredictionResponse(BaseModel):
    """Prediction metadata."""

    model_config = ConfigDict(
        extra="forbid",
    )

    filename: str
    duration_seconds: float
    detected_notes: int
    metrics: InferenceMetrics
    model: ModelInfo


class ModelResponse(BaseModel):
    """Loaded model information."""

    model_config = ConfigDict(
        extra="forbid",
    )

    name: str
    framework: str
    version: str
    input_shape: tuple[int, ...]
    output_shape: tuple[int, ...]
    threshold: float
    train_dataset: str | None = None
    description: str | None = None
