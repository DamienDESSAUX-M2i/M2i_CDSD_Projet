import logging
from dataclasses import dataclass
from time import perf_counter

import numpy as np
from core.model_manager import ModelManager, ModelMetadata
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class InferenceResult:
    probabilities: NDArray[np.float32]
    piano_roll: NDArray[np.bool_]
    threshold: float
    inference_time: float


class InferenceService:
    """Run inference using the trained TensorFlow model.

    The service reproduces the exact inference pipeline used during
    model validation:

        Features
            ↓
        RobustScaler
            ↓
        TensorFlow model
            ↓
        Probabilities
            ↓
        Threshold
            ↓
        Binary piano roll
    """

    def __init__(
        self, model_manager: ModelManager, model_metadata: ModelMetadata
    ) -> None:
        self._manager = model_manager
        self._metadata = model_metadata

    @property
    def model(self):
        return self._manager.model

    @property
    def scaler(self):
        return self._manager.scaler

    @property
    def threshold(self) -> float:
        return self._metadata.threshold

    def infer(
        self,
        features: NDArray[np.float32],
    ) -> InferenceResult:
        """Run complete inference.

        Args:
            features:
                Input feature matrix.

        Returns:
            InferenceResult:

                - Probability matrix with shape (n_frames, n_notes).
                - Binary piano roll.
                - Threshold.
                - Inference time in secondes.
        """

        logger.info("Running model inference.")

        t0 = perf_counter()

        scaled = self._manager.normalize_features(features)

        probabilities = self.model.predict(
            scaled,
            verbose=0,
        ).astype(np.float32)

        elapsed = perf_counter() - t0

        logger.info(f"Inference completed in {elapsed:.3f} s.")

        return InferenceResult(
            probabilities=probabilities,
            piano_roll=probabilities >= self.threshold,
            threshold=self.threshold,
            inference_time=elapsed,
        )
