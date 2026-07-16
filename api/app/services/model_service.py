from app.core import ModelManager
from app.models import ApiResponse, ModelResponse


def get_loaded_model_information(model_manager: ModelManager):
    """
    Returns model information.
    """

    meta = model_manager.metadata

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
        )
    )
