from app.models import (
    ApiResponse,
    HealthResponse,
    ModelResponse,
    PredictionRequest,
    PredictionResponse,
)
from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import FileResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=ApiResponse[HealthResponse],
    summary="Health check",
)
def health_check():
    """
    Check whether the API and the transcription model are ready.
    """

    return get_health_status()


@router.post(
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


@router.post(
    "/predict",
    response_model=ApiResponse[PredictionResponse],
    summary="Predict notes without returning a MIDI file",
)
async def predict_notes(
    audio_file: UploadFile = File(...),
    threshold: float | None = Query(
        default=None,
        ge=0.0,
        le=1.0,
    ),
):
    """
    Predict notes and return only inference metadata.
    """

    request = PredictionRequest(
        threshold=threshold,
    )

    return predict_audio_file(
        audio_file=audio_file,
        request=request,
    )


@router.get(
    "/model",
    response_model=ApiResponse[ModelResponse],
    summary="Get loaded model information",
)
def get_model():
    """
    Return information about the loaded transcription model.
    """

    return get_loaded_model_information()
