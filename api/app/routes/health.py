from fastapi import APIRouter, Depends

from app.core import ModelManager
from app.dependencies import get_model_manager
from app.models import ApiResponse, HealthResponse
from app.services.health_service import get_health_status

health_router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@health_router.get(
    "",
    response_model=ApiResponse[HealthResponse],
    summary="Health check",
)
def health_check(model_manager: ModelManager = Depends(get_model_manager)):
    """
    Check whether the API and the transcription model are ready.
    """

    return get_health_status(model_manager=model_manager)
