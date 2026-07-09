from app.models import ApiResponse, ModelResponse
from fastapi import APIRouter
from services import get_loaded_model_information

model_router = APIRouter(
    prefix="/model",
    tags=["Model"],
)


@model_router.get(
    "",
    response_model=ApiResponse[ModelResponse],
    summary="Get loaded model information",
)
def get_model():
    """
    Return information about the loaded transcription model.
    """

    return get_loaded_model_information()
