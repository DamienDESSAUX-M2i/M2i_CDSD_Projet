from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    """Inference parameters."""

    model_config = ConfigDict(
        extra="forbid",
    )

    threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Override default prediction threshold.",
    )
