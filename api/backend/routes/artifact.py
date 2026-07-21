import logging

from fastapi import APIRouter
from fastapi.responses import FileResponse

from backend.core import PROCESSING_SETTINGS
from backend.exceptions import ArtifactNotFound, InvalidArtifactPath

logger = logging.getLogger(__name__)


artifact_router = APIRouter(
    prefix="/artifacts",
    tags=["artifacts"],
)


def _get_artifact(
    prediction_id: str,
    filename: str,
    media_type: str,
    download_name: str | None = None,
) -> FileResponse:
    """Return a generated transcription artifact.

    Args:
        prediction_id:
            Unique transcription process identifier.

        filename:
            Artifact filename stored in the process directory.

        media_type:
            MIME type returned to the client.

        download_name:
            Optional filename exposed during download.

    Returns:
        FileResponse containing the requested artifact.

    Raises:
        HTTPException:
            If the artifact does not exist or the path is invalid.
    """

    output_dir = PROCESSING_SETTINGS.output_dir.resolve()

    artifact_path = (output_dir / prediction_id / filename).resolve()

    if not artifact_path.is_relative_to(output_dir):
        logger.warning(
            "Invalid artifact path requested: %s.",
            artifact_path,
        )

        raise InvalidArtifactPath()

    if not artifact_path.exists() or not artifact_path.is_file():
        logger.warning(
            "Artifact not found: %s.",
            artifact_path,
        )

        raise ArtifactNotFound()

    logger.debug(
        "Serving artifact: %s.",
        artifact_path,
    )

    return FileResponse(
        path=artifact_path,
        media_type=media_type,
        filename=download_name or filename,
    )


@artifact_router.get(
    "/{prediction_id}/midi",
    summary="Download generated MIDI file",
)
def get_midi(
    prediction_id: str,
) -> FileResponse:
    """Download generated MIDI transcription.

    Args:
        prediction_id:
            Transcription process identifier.

    Returns:
        MIDI file response.
    """
    return _get_artifact(
        prediction_id=prediction_id,
        filename="transcription.mid",
        media_type="audio/midi",
        download_name="transcription.mid",
    )


@artifact_router.get(
    "/{prediction_id}/piano-roll/png",
    summary="Download piano roll PNG image",
)
def get_piano_roll_png(
    prediction_id: str,
) -> FileResponse:
    """Download piano roll PNG rendering.

    Args:
        prediction_id:
            Transcription process identifier.

    Returns:
        PNG image response.
    """
    return _get_artifact(
        prediction_id=prediction_id,
        filename="piano_roll.png",
        media_type="image/png",
    )


@artifact_router.get(
    "/{prediction_id}/piano-roll/svg",
    summary="Download piano roll SVG image",
)
def get_piano_roll_svg(
    prediction_id: str,
) -> FileResponse:
    """Download piano roll SVG rendering.

    Args:
        prediction_id:
            Transcription process identifier.

    Returns:
        SVG image response.
    """
    return _get_artifact(
        prediction_id=prediction_id,
        filename="piano_roll.svg",
        media_type="image/svg+xml",
    )


@artifact_router.get(
    "/{prediction_id}/score/pdf",
    summary="Download generated PDF score",
)
def get_score_pdf(
    prediction_id: str,
) -> FileResponse:
    """Download generated PDF musical score.

    Args:
        prediction_id:
            Transcription process identifier.

    Returns:
        PDF file response.
    """
    return _get_artifact(
        prediction_id=prediction_id,
        filename="transcription.pdf",
        media_type="application/pdf",
    )


@artifact_router.get(
    "/{prediction_id}/score/svg",
    summary="Download generated SVG score",
)
def get_score_svg(
    prediction_id: str,
) -> FileResponse:
    """Download generated SVG musical score.

    Args:
        prediction_id:
            Transcription process identifier.

    Returns:
        SVG file response.
    """
    return _get_artifact(
        prediction_id=prediction_id,
        filename="transcription.svg",
        media_type="image/svg+xml",
    )
