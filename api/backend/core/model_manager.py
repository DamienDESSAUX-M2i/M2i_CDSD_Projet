import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

import joblib
import numpy as np
import tensorflow as tf
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class FeatureScaler(Protocol):
    """Protocol implemented by feature scalers."""

    def transform(
        self,
        features: NDArray[np.float32],
    ) -> NDArray[np.float32]:
        """Transform input features."""
        ...


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    """Metadata describing the trained model.

    Attributes:
        name:
            Model name.

        version:
            Model version.

        framework:
            Machine learning framework.

        input_shape:
            Expected model input shape.

        output_shape:
            Model output shape.

        threshold:
            Probability threshold used for binary classification.

        dataset:
            Training dataset name if available.

        description:
            Model description if available.
    """

    name: str
    version: str
    framework: str = "tensorflow"
    input_shape: tuple[int, ...] = ()
    output_shape: tuple[int, ...] = ()
    threshold: float = 0.5
    dataset: str | None = None
    description: str | None = None


class ModelManager:
    """Manage machine learning artifacts.

    This class loads the trained TensorFlow model, optional feature scaler
    and metadata once during application startup.

    Loaded artifacts are kept in memory and reused for inference.
    """

    def __init__(
        self,
        model_path: str | Path,
        scaler_path: str | Path | None = None,
        metadata_path: str | Path | None = None,
    ) -> None:
        """Initialize the model manager.

        Args:
            model_path:
                Path to the TensorFlow model.

            scaler_path:
                Optional path to the serialized feature scaler.

            metadata_path:
                Optional path to model metadata JSON file.

        Raises:
            FileNotFoundError:
                If the model file does not exist.
        """

        self._model_path: Path = Path(model_path)

        self._scaler_path: Path | None = (
            Path(scaler_path) if scaler_path is not None else None
        )

        self._metadata_path: Path | None = (
            Path(metadata_path) if metadata_path is not None else None
        )

        self.model: tf.keras.Model = self._load_model()
        self.scaler: FeatureScaler | None = self._load_scaler()
        self.metadata: ModelMetadata = self._load_metadata()

    def _load_model(self) -> tf.keras.Model:
        """Load TensorFlow model from disk.

        Returns:
            Loaded TensorFlow model.

        Raises:
            FileNotFoundError:
                If the model path does not exist.
            Exception:
                If TensorFlow cannot load the model.
        """

        logger.info(
            "Loading TensorFlow model from '%s'.",
            self._model_path,
        )

        if not self._model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self._model_path}",
            )

        try:
            model = tf.keras.models.load_model(
                self._model_path,
            )

        except Exception:
            logger.exception(
                "Unable to load TensorFlow model from '%s'.",
                self._model_path,
            )
            raise

        logger.info("TensorFlow model loaded successfully.")

        return model

    def _load_scaler(self) -> FeatureScaler | None:
        """Load feature scaler.

        Returns:
            Loaded scaler or None if unavailable.
        """

        if self._scaler_path is None:
            logger.debug("No scaler configured.")
            return None

        if not self._scaler_path.exists():
            logger.warning(
                "Scaler file does not exist: '%s'.",
                self._scaler_path,
            )
            return None

        logger.info(
            "Loading feature scaler from '%s'.",
            self._scaler_path,
        )

        try:
            scaler = joblib.load(self._scaler_path)

        except Exception:
            logger.exception(
                "Unable to load scaler from '%s'.",
                self._scaler_path,
            )
            raise

        return cast(FeatureScaler, scaler)

    def _load_metadata(self) -> ModelMetadata:
        """Load model metadata.

        Returns:
            Model metadata.

        Raises:
            ValueError:
                If metadata content is invalid.
        """

        if self._metadata_path is None:
            logger.warning(
                "No metadata file configured. Using default metadata.",
            )

            return ModelMetadata(
                name="unknown",
                version="0.0.0",
            )

        if not self._metadata_path.exists():
            logger.warning(
                "Metadata file does not exist: '%s'. Using default metadata.",
                self._metadata_path,
            )

            return ModelMetadata(
                name="unknown",
                version="0.0.0",
            )

        logger.info(
            "Loading model metadata from '%s'.",
            self._metadata_path,
        )

        try:
            with self._metadata_path.open(
                mode="r",
                encoding="utf-8",
            ) as metadata_file:
                data = json.load(metadata_file)

        except Exception:
            logger.exception(
                "Unable to load metadata from '%s'.",
                self._metadata_path,
            )
            raise

        return ModelMetadata(**data)

    def normalize_features(
        self,
        features: NDArray[np.float32],
    ) -> NDArray[np.float32]:
        """Normalize features before inference.

        Args:
            features:
                Raw extracted feature matrix.

        Returns:
            Normalized feature matrix.
        """

        if self.scaler is not None:
            logger.debug("Applying feature scaler.")

            return self.scaler.transform(
                features,
            ).astype(np.float32, copy=False)

        logger.debug(
            "No scaler configured. Applying fallback normalization.",
        )

        return ((features + 80.0) / 80.0).astype(np.float32, copy=False)

    def get_input_shape(self) -> tuple[int, ...]:
        """Return expected model input shape.

        Returns:
            Model input shape without batch dimension.
        """

        return tuple(self.model.input_shape[1:])

    def get_output_shape(self) -> tuple[int, ...]:
        """Return model output shape.

        Returns:
            Model output shape without batch dimension.
        """

        return tuple(self.model.output_shape[1:])
