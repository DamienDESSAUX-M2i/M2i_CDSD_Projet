import logging
import platform

import tensorflow as tf

from backend.core import ModelManager
from backend.models import ApiResponse, HealthResponse, HealthStatus

logger = logging.getLogger(__name__)


def get_health_status(
    model_manager: ModelManager,
) -> ApiResponse[HealthResponse]:
    """Retrieve the current application health status.

    Args:
        model_manager: Model manager used to determine whether the model has
            been successfully loaded.

    Returns:
        API response containing the application health information.
    """

    logger.debug("Collecting application health status.")

    try:
        model_loaded = model_manager.model is not None
        status = HealthStatus.OK if model_loaded else HealthStatus.DEGRADED

    except Exception:
        logger.exception("Failed to determine application health status.")
        status = HealthStatus.ERROR
        model_loaded = False

    device = "gpu" if tf.config.list_physical_devices("GPU") else "cpu"

    logger.debug(
        "Health status collected: status=%s, model_loaded=%s, device=%s.",
        status.value,
        model_loaded,
        device,
    )

    return ApiResponse(
        data=HealthResponse(
            status=status,
            model_loaded=model_loaded,
            tensorflow_version=tf.__version__,
            python_version=platform.python_version(),
            device=device,
        ),
    )
