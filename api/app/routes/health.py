import logging

from fastapi import APIRouter, Depends

from app.core import ModelManager
from app.dependencies import get_model_manager
from app.models import ApiResponse, HealthResponse
from app.services import get_health_status

logger = logging.getLogger(__name__)


health_router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@health_router.get(
    "",
    response_model=ApiResponse[HealthResponse],
    summary="Health check",
)
def health_check(
    model_manager: ModelManager = Depends(get_model_manager),
) -> ApiResponse[HealthResponse]:
    """Check API and model readiness.

    Args:
        model_manager:
            Loaded machine learning model manager injected by FastAPI.

    Returns:
        API health status including model availability.
    """
    logger.debug("Health check requested.")

    return get_health_status(
        model_manager=model_manager,
    )
