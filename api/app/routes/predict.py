from app.models import ApiResponse, PredictionRequest, PredictionResponse
from fastapi import APIRouter, File, Query, UploadFile

predict_router = APIRouter()


@predict_router.post(
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
