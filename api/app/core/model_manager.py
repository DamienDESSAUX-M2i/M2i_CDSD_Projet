import json
from dataclasses import dataclass
from pathlib import Path

import tensorflow as tf


@dataclass(frozen=True)
class ModelMetadata:
    name: str
    version: str
    framework: str = "tensorflow"
    input_shape: tuple[int, ...] = ()
    output_shape: tuple[int, ...] = ()
    threshold: float = 0.5
    dataset: str | None = None
    description: str | None = None


class ModelManager:
    """
    Singleton-like manager for ML artifacts.
    Loads model once at API startup and exposes read-only access.
    """

    _instance: "ModelManager | None" = None

    def __init__(
        self,
        model_path: str | Path,
        scaler_path: str | Path | None = None,
        metadata_path: str | Path | None = None,
    ):
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path) if scaler_path else None
        self.metadata_path = Path(metadata_path) if metadata_path else None

        self.model: tf.keras.Model = self._load_model()
        self.metadata = self._load_metadata()

    # -------------------
    # Singleton access
    # -------------------

    @classmethod
    def get_instance(cls) -> "ModelManager":
        if cls._instance is None:
            raise RuntimeError(
                "ModelManager not initialized. Call ModelManager.init() first."
            )
        return cls._instance

    @classmethod
    def init(
        cls,
        model_path: str | Path,
        scaler_path: str | Path | None = None,
        metadata_path: str | Path | None = None,
    ) -> "ModelManager":
        cls._instance = cls(model_path, scaler_path, metadata_path)
        return cls._instance

    # -------------------
    # Loaders
    # -------------------

    def _load_model(self) -> tf.keras.Model:
        return tf.keras.models.load_model(self.model_path)

    def _load_metadata(self) -> ModelMetadata:
        if self.metadata_path and self.metadata_path.exists():
            with open(self.metadata_path, "r") as f:
                data = json.load(f)
            return ModelMetadata(**data)

        # fallback minimal metadata
        return ModelMetadata(
            name="unknown",
            version="0.0.0",
        )

    # -------------------
    # Helpers
    # -------------------

    def get_input_shape(self) -> tuple[int, ...]:
        return tuple(self.model.input_shape[1:])

    def get_output_shape(self) -> tuple[int, ...]:
        return tuple(self.model.output_shape[1:])
