import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.models import ApiResponse, ErrorDetails, ResponseStatus

from .api_exceptions import APIError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(APIError)
    async def api_exception_handler(
        request: Request,
        exc: APIError,
    ) -> JSONResponse:
        logger.warning(
            "%s %s -> %s",
            request.method,
            request.url.path,
            exc.message,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=ApiResponse(
                success=ResponseStatus.ERROR,
                error=ErrorDetails(
                    code=exc.code,
                    message=exc.message,
                ),
            ).model_dump(mode="json"),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiResponse(
                success=ResponseStatus.ERROR,
                error=ErrorDetails(
                    code="HTTP_ERROR",
                    message=str(exc.detail),
                ),
            ).model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled exception.")

        return JSONResponse(
            status_code=500,
            content=ApiResponse(
                success=ResponseStatus.ERROR,
                error=ErrorDetails(
                    code="INTERNAL_SERVER_ERROR",
                    message="An unexpected error occurred.",
                ),
            ).model_dump(mode="json"),
        )
