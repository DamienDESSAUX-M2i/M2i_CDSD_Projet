from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from backend.core import TIME_ZONE

T = TypeVar("T")


class ResponseStatus(StrEnum):
    """Generic API response status."""

    SUCCESS = "success"
    ERROR = "error"


class HealthStatus(StrEnum):
    """Application health status."""

    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


def current_time() -> datetime:
    """Return the current application timestamp.

    Returns:
        Current datetime localized to the application timezone.
    """

    return datetime.now(TIME_ZONE)


class ApiBaseModel(BaseModel):
    """Base model configuration for API schemas."""

    model_config = ConfigDict(
        extra="forbid",
        # frozen=True,
    )


class ErrorDetails(ApiBaseModel):
    """API error description.

    Attributes:
        code:
            Error code.

        message:
            Error message.
    """

    code: str
    message: str


class ApiResponse(ApiBaseModel, Generic[T]):
    """Generic API response envelope.

    Attributes:
        success:
            Response status.

        timestamp:
            Response creation timestamp.

        data:
            Response payload.

        error:
            Response error.
    """

    success: ResponseStatus = ResponseStatus.SUCCESS

    timestamp: datetime = Field(
        default_factory=current_time,
    )

    data: T | None = None

    error: ErrorDetails | None = None


class InferenceMetrics(ApiBaseModel):
    """Execution timing metrics for transcription pipeline.

    Attributes:
        preprocessing_seconds:
            Audio preprocessing duration.

        inference_seconds:
            Neural network inference duration.

        postprocessing_seconds:
            Artifact generation duration.

        total_seconds:
            Complete pipeline duration.
    """

    preprocessing_seconds: float
    inference_seconds: float
    postprocessing_seconds: float
    total_seconds: float

    @field_validator(
        "preprocessing_seconds",
        "inference_seconds",
        "postprocessing_seconds",
        "total_seconds",
    )
    @classmethod
    def validate_duration(
        cls,
        value: float,
    ) -> float:
        """Validate execution duration.

        Args:
            value:
                Duration value.

        Returns:
            Validated duration.

        Raises:
            ValueError:
                If duration is negative.
        """

        if value < 0:
            raise ValueError("Duration cannot be negative.")

        return value


class ModelInfo(ApiBaseModel):
    """Information about the loaded ML model.

    Attributes:
        name:
            Model identifier.

        framework:
            Machine learning framework.

        version:
            Model version.

        input_shape:
            Expected model input shape.

        output_shape:
            Model output shape.

        threshold:
            Classification threshold.
    """

    name: str

    framework: str = "tensorflow"

    version: str

    input_shape: tuple[int, ...]

    output_shape: tuple[int, ...]

    threshold: float

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, value: float) -> float:
        """Validate classification threshold.

        Args:
            value:
                Probability threshold.

        Returns:
            Validated threshold.

        Raises:
            ValueError:
                If threshold is outside [0, 1].
        """

        if not 0 <= value <= 1:
            raise ValueError("Threshold must be between 0 and 1.")

        return value
