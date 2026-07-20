import logging

from fastapi import APIRouter, Depends

from app.core import ModelManager
from app.dependencies import get_model_manager
from app.models import ApiResponse, ModelResponse
from app.services import get_loaded_model_information

logger = logging.getLogger(__name__)


model_router = APIRouter(
    prefix="/model",
    tags=["model"],
)


@model_router.get(
    "",
    response_model=ApiResponse[ModelResponse],
    summary="Get loaded model information",
)
def get_model_information(
    model_manager: ModelManager = Depends(get_model_manager),
) -> ApiResponse[ModelResponse]:
    """Return information about the loaded transcription model.

    Args:
        model_manager:
            Loaded machine learning model manager injected by FastAPI.

    Returns:
        API response containing model metadata and input/output shapes.
    """
    logger.debug("Model information requested.")

    return get_loaded_model_information(
        model_manager=model_manager,
    )
