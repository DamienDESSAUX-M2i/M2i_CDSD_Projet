import logging

from app.core import PROCESSING_SETTINGS
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)


artifact_router = APIRouter(
    prefix="/artifacts",
    tags=["Artifacts"],
)


def _get_artifact(
    prediction_id: str,
    filename: str,
    media_type: str,
    download_name: str | None = None,
) -> FileResponse:
    """
    Return an artifact file.

    Args:
        prediction_id:
            Tracking process.

        filename:
            Artifact filename.

        media_type:
            MIME type returned to the client.

        download_name:
            Optional filename exposed to the client.

    Returns:
        FileResponse containing the artifact.

    Raises:
        HTTPException:
            If artifact does not exist.
    """

    artifact_path = PROCESSING_SETTINGS.output_dir / prediction_id / filename

    if not artifact_path.exists():
        logger.warning("Artifact not found: %s", artifact_path)

        raise HTTPException(status_code=404, detail="Artifact not found.")

    return FileResponse(
        path=artifact_path,
        media_type=media_type,
        filename=download_name or filename,
    )


@artifact_router.get("/{prediction_id}/midi", summary="Download generated MIDI file")
def get_midi(prediction_id: str) -> FileResponse:
    """
    Download generated MIDI transcription.
    """

    return _get_artifact(
        prediction_id=prediction_id,
        filename="transcription.mid",
        media_type="audio/midi",
        download_name="transcription.mid",
    )


@artifact_router.get(
    "/{prediction_id}/piano-roll/png", summary="Download piano roll PNG image"
)
def get_piano_roll_png(prediction_id: str) -> FileResponse:
    """
    Download piano roll PNG rendering.
    """

    return _get_artifact(
        prediction_id=prediction_id,
        filename="piano_roll.png",
        media_type="image/png",
    )


@artifact_router.get(
    "/{prediction_id}/piano-roll/svg", summary="Download piano roll SVG image"
)
def get_piano_roll_svg(prediction_id: str) -> FileResponse:
    """
    Download piano roll SVG rendering.
    """

    return _get_artifact(
        prediction_id=prediction_id,
        filename="piano_roll.svg",
        media_type="image/svg+xml",
    )


@artifact_router.get(
    "/{prediction_id}/score/pdf", summary="Download generated PDF score"
)
def get_score_pdf(prediction_id: str) -> FileResponse:
    """
    Download generated PDF musical score.
    """

    return _get_artifact(
        prediction_id=prediction_id,
        filename="transcription.pdf",
        media_type="application/pdf",
    )


@artifact_router.get(
    "/{prediction_id}/score/svg", summary="Download generated SVG score"
)
def get_score_svg(prediction_id: str) -> FileResponse:
    """
    Download generated SVG musical score.
    """

    return _get_artifact(
        prediction_id=prediction_id,
        filename="transcription.svg",
        media_type="image/svg+xml",
    )
