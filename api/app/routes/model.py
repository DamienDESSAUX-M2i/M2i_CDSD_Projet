from app.models import ApiResponse, ModelResponse
from fastapi import APIRouter

model_router = APIRouter()


@model_router.get(
    "/model",
    response_model=ApiResponse[ModelResponse],
    summary="Get loaded model information",
)
def get_model():
    """
    Return information about the loaded transcription model.
    """

    return get_loaded_model_information()
