from typing import Literal

from pydantic import (
    Field,
    field_validator,
)

from .common import ApiBaseModel, HealthStatus, InferenceMetrics, ModelInfo


class HealthResponse(ApiBaseModel):
    """Application health information.

    Attributes:
        status:
            Current API health status.

        model_loaded:
            Whether the ML model is loaded.

        tensorflow_version:
            Installed TensorFlow version.

        python_version:
            Running Python version.

        device:
            Computation device used by TensorFlow.
    """

    status: HealthStatus

    model_loaded: bool

    tensorflow_version: str

    python_version: str

    device: Literal["gpu", "cpu"]


class ModelResponse(ApiBaseModel):
    """Information about the loaded transcription model.

    Attributes:
        name:
            Model name.

        framework:
            ML framework used for inference.

        version:
            Model version.

        input_shape:
            Expected model input dimensions.

        output_shape:
            Model output dimensions.

        threshold:
            Classification threshold.

        train_dataset:
            Dataset used during training.

        description:
            Human-readable model description.
    """

    name: str

    framework: str

    version: str

    input_shape: tuple[int, ...]

    output_shape: tuple[int, ...]

    threshold: float = Field(ge=0.0, le=1.0)

    train_dataset: str | None = None

    description: str | None = None


class PredictionResponse(ApiBaseModel):
    """Result of an audio transcription request.

    Contains generated musical artifacts and execution metrics.

    Attributes:
        processing_id:
            Unique identifier of the transcription process.

        detected_notes:
            Number of detected note events.

        quantized_notes:
            Number of rhythmically quantized notes.

        midi_path:
            Generated MIDI artifact path.

        piano_roll_png_path:
            PNG piano-roll visualization path.

        piano_roll_svg_path:
            SVG piano-roll visualization path.

        score_pdf_path:
            Generated PDF score path.

        score_svg_path:
            Generated SVG score path.

        metrics:
            Pipeline execution metrics.

        model:
            Model information used for inference.
    """

    processing_id: str

    detected_notes: int = Field(ge=0)

    quantized_notes: int = Field(ge=0)

    midi_path: str | None = None

    piano_roll_png_path: str | None = None

    piano_roll_svg_path: str | None = None

    score_pdf_path: str | None = None

    score_svg_path: str | None = None

    metrics: InferenceMetrics

    model: ModelInfo

    @field_validator("processing_id")
    @classmethod
    def validate_processing_id(
        cls,
        value: str,
    ) -> str:
        """Ensure processing identifier is not empty.

        Args:
            value:
                Processing identifier.

        Returns:
            Validated identifier.

        Raises:
            ValueError:
                If identifier is empty.
        """

        if not value.strip():
            raise ValueError(
                "Processing ID cannot be empty.",
            )

        return value
