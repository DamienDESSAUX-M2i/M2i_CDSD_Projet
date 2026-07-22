import logging

from fastapi import APIRouter

from backend.core import ModelManager
from backend.dependencies import ModelManagerDep
from backend.models import ApiResponse, ModelResponse
from backend.services import get_loaded_model_information

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
    model_manager: ModelManager = ModelManagerDep,  # type: ignore
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
