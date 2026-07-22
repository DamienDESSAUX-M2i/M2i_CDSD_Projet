import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from backend.core import ModelManager
from backend.dependencies import (
    FileDep,
    ModelManagerDep,
    PredictionServiceDep,
)
from backend.exceptions import InvalidAudioError, PredictionFailedError
from backend.models import (
    ApiResponse,
    InferenceMetrics,
    ModelInfo,
    PredictionResponse,
)
from backend.services import PredictionService

logger = logging.getLogger(__name__)


predict_router = APIRouter(
    prefix="/predict",
    tags=["prediction"],
)


@predict_router.post(
    "",
    response_model=ApiResponse[PredictionResponse],
    summary="Run audio transcription",
)
async def predict(
    file: UploadFile = FileDep,  # type: ignore
    model_manager: ModelManager = ModelManagerDep,  # type: ignore
    prediction_service: PredictionService = PredictionServiceDep,  # type: ignore
) -> ApiResponse[PredictionResponse]:
    """Run the complete audio transcription pipeline.

    The pipeline executes:

        1. Audio preprocessing.
        2. Neural network inference.
        3. Musical post-processing.

    Args:
        file:
            Uploaded WAV audio file.

        model_manager:
            Loaded machine learning model manager.

        prediction_service:
            Audio transcription orchestration service.

    Returns:
        Generated transcription artifacts and processing metrics.

    Raises:
        HTTPException:
            If the uploaded file is invalid or processing fails.
    """

    logger.info(
        "Prediction request received: filename='%s'.",
        file.filename,
    )

    if file.content_type not in {
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
    }:
        logger.warning(
            "Rejected file with unsupported content type: %s.",
            file.content_type,
        )

        raise InvalidAudioError()

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as temporary_file:
            shutil.copyfileobj(
                file.file,
                temporary_file,
            )

            temporary_path = Path(
                temporary_file.name,
            )

        await file.close()

        result = await run_in_threadpool(
            prediction_service.predict,
            temporary_path,
        )

        postprocessing = result.postprocessing

        total_time = (
            result.preprocessing.preprocessing_time
            + result.inference.inference_time
            + postprocessing.postprocessing_time
        )

        logger.info(
            (
                "Prediction completed successfully "
                "(processing_id=%s, total_time=%.3f s)."
            ),
            result.processing_id,
            total_time,
        )

        return ApiResponse(
            data=PredictionResponse(
                processing_id=result.processing_id,
                detected_notes=len(postprocessing.notes),
                quantized_notes=len(
                    postprocessing.quantized_notes,
                ),
                midi_path=str(postprocessing.midi_path),
                piano_roll_png_path=str(
                    postprocessing.piano_roll_png_path,
                ),
                piano_roll_svg_path=str(
                    postprocessing.piano_roll_svg_path,
                ),
                score_pdf_path=(
                    str(postprocessing.score_pdf_path)
                    if postprocessing.score_pdf_path
                    else None
                ),
                score_svg_path=(
                    str(postprocessing.score_svg_path)
                    if postprocessing.score_svg_path
                    else None
                ),
                metrics=InferenceMetrics(
                    preprocessing_seconds=(result.preprocessing.preprocessing_time),
                    inference_seconds=(result.inference.inference_time),
                    postprocessing_seconds=(postprocessing.postprocessing_time),
                    total_seconds=total_time,
                ),
                model=ModelInfo(
                    name=model_manager.metadata.name,
                    framework=model_manager.metadata.framework,
                    version=model_manager.metadata.version,
                    input_shape=model_manager.metadata.input_shape,
                    output_shape=model_manager.metadata.output_shape,
                    threshold=model_manager.metadata.threshold,
                ),
            ),
        )

    except HTTPException:
        raise

    except Exception as exception:
        logger.exception("Prediction failed.")

        raise PredictionFailedError() from exception

    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

            logger.debug(
                "Temporary audio file removed: '%s'.",
                temporary_path,
            )
