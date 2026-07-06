from app.core import ModelManager
from app.routes import router
from fastapi import FastAPI

app = FastAPI(title="Guitar Transcription API")


@app.on_event("startup")
def load_model():
    ModelManager.init(
        model_path="artifacts/model.keras",
        scaler_path="artifacts/scaler.joblib",
        metadata_path="artifacts/metadata.json",
    )


app.include_router(router)
