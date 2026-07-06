from app.models import PredictionRequest
from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import FileResponse

transcribe_router = APIRouter()


@transcribe_router.post(
    "/transcribe",
    response_class=FileResponse,
    summary="Transcribe a WAV file into MIDI",
)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    threshold: float | None = Query(
        default=None,
        ge=0.0,
        le=1.0,
    ),
):
    """
    Transcribe an audio file and return the generated MIDI file.
    """

    request = PredictionRequest(
        threshold=threshold,
    )

    return transcribe_audio_file(
        audio_file=audio_file,
        request=request,
    )
