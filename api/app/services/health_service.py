import platform

import tensorflow as tf
from app.core import ModelManager
from app.models import ApiResponse, HealthResponse, HealthStatus


def get_health_status() -> ApiResponse[HealthResponse]:
    """
    Returns system health information.
    """

    try:
        manager = ModelManager.get_instance()
        model_loaded = manager.model is not None

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
