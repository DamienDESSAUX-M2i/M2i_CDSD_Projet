from core import ModelManager
from fastapi import Request
from services import PredictionService


def get_model_manager(
    request: Request,
) -> ModelManager:
    """
    Retrieve initialized model manager.

    Args:
        request:
            FastAPI request object.

    Returns:
        Shared ModelManager instance.
    """

    return request.app.state.model_manager


def get_prediction_service(
    request: Request,
) -> PredictionService:
    """
    Retrieve initialized prediction service.

    Args:
        request:
            FastAPI request object.

    Returns:
        Shared PredictionService instance.
    """

    return request.app.state.prediction_service
