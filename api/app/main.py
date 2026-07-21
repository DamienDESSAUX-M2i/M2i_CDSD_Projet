import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.core import PROCESSING_SETTINGS, ModelManager, configure_logging
from app.exceptions.handlers import register_exception_handlers
from app.routes import router
from app.services import (
    InferenceService,
    PostprocessingService,
    PredictionService,
    PreprocessingService,
)
from fastapi import FastAPI

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage the application lifecycle.

    Initialize all application services during startup and release resources
    during shutdown.

    Args:
        app: FastAPI application instance.

    Yields:
        Control to the running application.
    """

    logger.info("Starting application initialization.")

    logger.info("Initializing model manager.")
    logger.debug(
        "Loading model from '%s' with scaler '%s' and metadata '%s'.",
        PROCESSING_SETTINGS.model_path,
        PROCESSING_SETTINGS.scaler_path,
        PROCESSING_SETTINGS.metadata_path,
    )

    model_manager = ModelManager(
        model_path=PROCESSING_SETTINGS.model_path,
        scaler_path=PROCESSING_SETTINGS.scaler_path,
        metadata_path=PROCESSING_SETTINGS.metadata_path,
    )

    logger.info("Model manager initialized successfully.")

    logger.info("Initializing preprocessing service.")
    preprocessing_service = PreprocessingService(
        settings=PROCESSING_SETTINGS,
    )

    logger.info("Initializing inference service.")
    inference_service = InferenceService(
        model_manager=model_manager,
    )

    logger.info("Initializing postprocessing service.")
    postprocessing_service = PostprocessingService(
        settings=PROCESSING_SETTINGS,
    )

    logger.info("Initializing prediction service.")
    prediction_service = PredictionService(
        preprocessing_service=preprocessing_service,
        inference_service=inference_service,
        postprocessing_service=postprocessing_service,
    )

    logger.debug("Registering services in FastAPI application state.")

    app.state.model_manager = model_manager
    app.state.preprocessing_service = preprocessing_service
    app.state.inference_service = inference_service
    app.state.postprocessing_service = postprocessing_service
    app.state.prediction_service = prediction_service

    logger.info("Application initialization completed.")

    yield

    logger.info("Application shutdown completed.")


app = FastAPI(
    title="Automatic Music Transcription API",
    description="Audio transcription API based on deep learning and CQT features.",
    version="1.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(router)
