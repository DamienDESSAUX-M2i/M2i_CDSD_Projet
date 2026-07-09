from pydantic import BaseModel, ConfigDict


class PredictionRequest(BaseModel):
    """Inference parameters."""

    model_config = ConfigDict(
        extra="forbid",
    )
