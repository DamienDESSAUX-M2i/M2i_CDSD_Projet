from fastapi import APIRouter

from .artifact import artifact_router
from .health import health_router as health_router
from .model import model_router as model_router
from .predict import predict_router as predict_router

router = APIRouter()

router.include_router(health_router)
router.include_router(model_router)
router.include_router(predict_router)
router.include_router(artifact_router)

__all__ = [
    "router",
]
