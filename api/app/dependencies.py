from typing import cast

from fastapi import Request

from app.core import ModelManager
from app.services import PredictionService


def get_model_manager(
    request: Request,
) -> ModelManager:
    """Retrieve the initialized model manager.

    The model manager is created once during application startup
    and stored in the FastAPI application state.

    Args:
        request:
            Current FastAPI request.

    Returns:
        Shared ModelManager instance.

    Raises:
        RuntimeError:
            If the model manager has not been initialized.
    """
    try:
        model_manager = request.app.state.model_manager

    except AttributeError as exc:
        raise RuntimeError(
            "ModelManager is not initialized.",
        ) from exc

    return cast(
        ModelManager,
        model_manager,
    )


def get_prediction_service(
    request: Request,
) -> PredictionService:
    """Retrieve the initialized prediction service.

    The prediction service is created once during application startup
    and reused for all prediction requests.

    Args:
        request:
            Current FastAPI request.

    Returns:
        Shared PredictionService instance.

    Raises:
        RuntimeError:
            If the prediction service has not been initialized.
    """
    try:
        prediction_service = request.app.state.prediction_service

    except AttributeError as exc:
        raise RuntimeError(
            "PredictionService is not initialized.",
        ) from exc

    return cast(
        PredictionService,
        prediction_service,
    )
