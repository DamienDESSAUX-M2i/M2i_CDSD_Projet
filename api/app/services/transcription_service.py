from app.models import PredictionRequest
from fastapi import UploadFile
from fastapi.responses import FileResponse


async def transcribe_audio_file(
    audio_file: UploadFile,
    request: PredictionRequest,
) -> FileResponse: ...
