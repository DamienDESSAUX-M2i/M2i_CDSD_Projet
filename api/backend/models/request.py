from .common import ApiBaseModel


class PredictionRequest(ApiBaseModel):
    """Parameters for an audio transcription request.

    This model currently acts as a validation boundary for future
    transcription options.

    Additional fields can be added here when configurable inference
    parameters are exposed through the API.
    """

    ...
