import logging
from contextlib import asynccontextmanager

from core import PROCESSING_SETTINGS, ModelManager
from fastapi import FastAPI
from routes import router
from services import (
    InferenceService,
    PostprocessingService,
    PredictionService,
    PreprocessingService,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Responsible for initializing and releasing application resources.

    During startup:
        - Load machine learning model.
        - Initialize preprocessing pipeline.
        - Initialize inference service.
        - Initialize postprocessing pipeline.
        - Register PredictionService.

    During shutdown:
        - Release resources if necessary.
    """

    logger.info("Starting application initialization.")

    logger.info("Loading model.")

    model_manager = ModelManager(
        model_path=PROCESSING_SETTINGS.model_path,
        scaler_path=PROCESSING_SETTINGS.scaler_path,
        metadata_path=PROCESSING_SETTINGS.metadata_path,
    )

    logger.info("Model loaded successfully.")

    preprocessing_service = PreprocessingService(
        settings=PROCESSING_SETTINGS,
    )

    inference_service = InferenceService(
        model_manager=model_manager,
    )

    postprocessing_service = PostprocessingService(
        settings=PROCESSING_SETTINGS,
    )

    prediction_service = PredictionService(
        preprocessing_service=preprocessing_service,
        inference_service=inference_service,
        postprocessing_service=postprocessing_service,
    )

    app.state.model_manager = model_manager

    app.state.preprocessing_service = preprocessing_service
    app.state.inference_service = inference_service
    app.state.postprocessing_service = postprocessing_service
    app.state.prediction_service = prediction_service

    logger.info("Application initialization completed.")

    yield

    logger.info("Application shutdown.")


app = FastAPI(
    title="Automatic Music Transcription API",
    description=("Audio transcription API based on deep learning and CQT features."),
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(router)
