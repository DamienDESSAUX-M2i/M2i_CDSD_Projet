from app.models import ApiResponse, PredictionRequest, PredictionResponse
from fastapi import UploadFile


async def predict_audio_file(
    audio_file: UploadFile,
    request: PredictionRequest,
) -> ApiResponse[PredictionResponse]: ...
