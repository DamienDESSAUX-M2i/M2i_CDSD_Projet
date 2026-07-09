from core import ModelManager
from models import ApiResponse, ModelResponse


def get_loaded_model_information():
    """
    Returns model information.
    """

    manager = ModelManager.get_instance()

    meta = manager.metadata

    return ApiResponse(
        data=ModelResponse(
            name=meta.name,
            framework=meta.framework,
            version=meta.version,
            input_shape=manager.get_input_shape(),
            output_shape=manager.get_output_shape(),
            threshold=meta.threshold,
            train_dataset=meta.dataset,
            description=meta.description,
        )
    )
