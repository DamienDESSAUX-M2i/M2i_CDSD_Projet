from fastapi import APIRouter, Depends

from app.core import ModelManager
from app.dependencies import get_model_manager
from app.models import ApiResponse, ModelResponse
from app.services import get_loaded_model_information

model_router = APIRouter(
    prefix="/model",
    tags=["Model"],
)


@model_router.get(
    "",
    response_model=ApiResponse[ModelResponse],
    summary="Get loaded model information",
)
def get_model(model_manager: ModelManager = Depends(get_model_manager)):
    """
    Return information about the loaded transcription model.
    """

    return get_loaded_model_information(model_manager=model_manager)
