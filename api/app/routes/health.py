from app.models import ApiResponse, HealthResponse
from app.services.health_service import get_health_status
from fastapi import APIRouter

health_router = APIRouter()


@health_router.get(
    "/health",
    response_model=ApiResponse[HealthResponse],
    summary="Health check",
)
def health_check():
    """
    Check whether the API and the transcription model are ready.
    """

    return get_health_status()
