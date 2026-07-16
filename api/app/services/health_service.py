import platform

import tensorflow as tf

from app.core import ModelManager
from app.models import ApiResponse, HealthResponse, HealthStatus


def get_health_status(model_manager: ModelManager) -> ApiResponse[HealthResponse]:
    """
    Returns system health information.
    """

    try:
        model_loaded = model_manager.model is not None

        status = HealthStatus.OK if model_loaded else HealthStatus.DEGRADED

    except Exception:
        status = HealthStatus.ERROR
        model_loaded = False

    return ApiResponse(
        data=HealthResponse(
            status=status,
            model_loaded=model_loaded,
            tensorflow_version=tf.__version__,
            python_version=platform.python_version(),
            device="gpu" if tf.config.list_physical_devices("GPU") else "cpu",
        )
    )
