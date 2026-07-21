import logging

from backend.core import ModelManager, ModelMetadata
from backend.models import ApiResponse, ModelResponse

logger = logging.getLogger(__name__)


def get_loaded_model_information(
    model_manager: ModelManager,
) -> ApiResponse[ModelResponse]:
    """Retrieve information about the loaded machine learning model.

    Args:
        model_manager: Model manager containing the loaded model and its
            metadata.

    Returns:
        API response containing the model information.
    """

    logger.debug("Retrieving loaded model information.")

    meta: ModelMetadata = model_manager.metadata

    return ApiResponse(
        data=ModelResponse(
            name=meta.name,
            framework=meta.framework,
            version=meta.version,
            input_shape=model_manager.get_input_shape(),
            output_shape=model_manager.get_output_shape(),
            threshold=meta.threshold,
            train_dataset=meta.dataset,
            description=meta.description,
        ),
    )
