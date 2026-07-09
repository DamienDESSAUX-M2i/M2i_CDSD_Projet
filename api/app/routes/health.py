from app.models import ApiResponse, HealthResponse
from app.services.health_service import get_health_status
from fastapi import APIRouter

health_router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@health_router.get(
    "",
    response_model=ApiResponse[HealthResponse],
    summary="Health check",
)
def health_check():
    """
    Check whether the API and the transcription model are ready.
    """

    return get_health_status()
