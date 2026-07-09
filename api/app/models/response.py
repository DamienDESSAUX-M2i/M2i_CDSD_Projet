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


class PredictionResponse(BaseModel):
    """Prediction API response."""

    model_config = ConfigDict(
        extra="forbid",
    )

    processing_id: str

    detected_notes: int
    quantized_notes: int

    midi_path: str | None
    piano_roll_png_path: str | None
    piano_roll_svg_path: str | None

    score_pdf_path: str | None
    score_svg_path: str | None

    metrics: InferenceMetrics
    model: ModelInfo
