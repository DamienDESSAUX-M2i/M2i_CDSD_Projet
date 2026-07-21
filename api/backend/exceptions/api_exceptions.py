from fastapi import status


class ApiException(Exception):
    """Base API exception."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        status_code: int,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code

        super().__init__(message)


class InvalidArtifactPath(ApiException):
    """Invalid artifact path exception."""

    def __init__(self) -> None:
        super().__init__(
            message="Invalid artifact path.",
            code="INVALID_ARTIFACT_PATH",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ArtifactNotFound(ApiException):
    """Artifact not found exception."""

    def __init__(self) -> None:
        super().__init__(
            message="Artifact not found.",
            code="ARTIFACT_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class InvalidAudio(ApiException):
    """Invalid audio exception."""

    def __init__(self) -> None:
        super().__init__(
            message="Only WAV files are supported.",
            code="INVALID_AUDIO",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class PredictionFailed(ApiException):
    """Prediction failed exception."""

    def __init__(self) -> None:
        super().__init__(
            message="Prediction failed.",
            code="PREDICTION_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
