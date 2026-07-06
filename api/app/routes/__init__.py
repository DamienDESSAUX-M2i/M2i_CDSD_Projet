from fastapi import APIRouter

from .health import health_router as health_router
from .model import model_router as model_router
from .predict import predict_router as predict_router
from .transcribe import transcribe_router as transcribe_router

router = APIRouter()

router.include_router(health_router)
router.include_router(model_router)
router.include_router(predict_router)
router.include_router(transcribe_router)

__all__ = [
    "router",
]
