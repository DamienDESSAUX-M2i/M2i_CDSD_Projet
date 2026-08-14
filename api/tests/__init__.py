import pathlib

API_DIR = pathlib.Path(__file__).parent.parent.resolve()
ARTIFACT_DIR = API_DIR / "backend" / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "model.keras"
SCALER_PATH = None
METADATA_PATH = ARTIFACT_DIR / "metadata.json"

DATA_FOLDER_PATH = pathlib.Path(__file__).parent.resolve() / "data"
