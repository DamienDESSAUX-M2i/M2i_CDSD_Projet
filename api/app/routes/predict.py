import logging
import shutil
import tempfile
from pathlib import Path

from core import ModelManager
from dependencies import get_model_manager, get_prediction_service
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from models import ApiResponse, InferenceMetrics, ModelInfo, PredictionResponse
from services.prediction_service import PredictionService

logger = logging.getLogger(__name__)


predict_router = APIRouter(
    prefix="/predict",
    tags=["Prediction"],
)


@predict_router.post(
    "",
    response_model=PredictionResponse,
)
async def predict(
    file: UploadFile = File(...),
    model_manager: ModelManager = Depends(get_model_manager),
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> ApiResponse[PredictionResponse]:
    """
    Run audio transcription pipeline.

    Args:
        file:
            Uploaded WAV audio file.

        service:
            Prediction pipeline service.

    Returns:
        Generated transcription artifacts and metrics.

    Raises:
        HTTPException:
            If prediction fails.
    """

    if file.content_type not in (
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
    ):
        raise HTTPException(
            status_code=400,
            detail="Only WAV files are supported.",
        )

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporary_file:
            shutil.copyfileobj(file.file, temporary_file)

            temporary_path = Path(temporary_file.name)

        result = prediction_service.predict(temporary_path)

        postprocessing = result.postprocessing

        return ApiResponse(
            data=PredictionResponse(
                processing_id=result.processing_id,
                detected_notes=len(postprocessing.notes),
                quantized_notes=len(postprocessing.quantized_notes),
                midi_path=str(postprocessing.midi_path),
                piano_roll_png_path=str(postprocessing.piano_roll_png_path),
                piano_roll_svg_path=str(postprocessing.piano_roll_svg_path),
                score_pdf_path=str(postprocessing.score_pdf_path),
                score_svg_path=str(postprocessing.score_svg_path),
                metrics=InferenceMetrics(
                    preprocessing_secondes=result.preprocessing.preprocessing_time,
                    inference_secondes=result.inference.inference_time,
                    postprocessing_secondes=postprocessing.postprocessing_time,
                    total_secondes=(
                        result.preprocessing.preprocessing_time
                        + postprocessing.postprocessing_time
                        + postprocessing.postprocessing_time
                    ),
                ),
                model=ModelInfo(
                    name=model_manager.metadata.name,
                    framework=model_manager.metadata.framework,
                    version=model_manager.metadata.version,
                    input_shape=model_manager.metadata.input_shape,
                    output_shape=model_manager.metadata.output_shape,
                    threshold=model_manager.metadata.threshold,
                ),
            )
        )

    except Exception as exc:
        logger.exception("Prediction failed.")

        raise HTTPException(status_code=500, detail="Prediction failed.") from exc

    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
