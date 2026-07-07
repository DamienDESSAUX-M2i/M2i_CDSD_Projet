import logging

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class ContextWindowBuilder:
    """
    Builds temporal context windows for frame-wise audio features.

    Output format: (n_frames, 2 * context_size + 1, n_features)

    This format preserves:
        - temporal structure
        - feature locality
        - CNN/RCNN compatibility
    """

    def __init__(self, context_size: int):
        self.context_size = context_size

    def build_context_windows(
        self,
        features: NDArray[np.float32],
    ) -> NDArray[np.float32]:
        """
        Parameters
        ----------
        features:
            Shape: (n_frames, n_features)

        Returns
        -------
        NDArray[np.float32]
            Shape: (n_frames, context_window, n_features)
        """

        if features.size == 0:
            raise ValueError("Input features array is empty.")

        if features.ndim != 2:
            raise ValueError(
                f"Expected 2D array (n_frames, n_features), got shape={features.shape}"
            )

        padding = self.context_size
        window_size = 2 * padding + 1

        padded = np.pad(
            features,
            pad_width=((padding, padding), (0, 0)),
            mode="edge",
        )

        n_frames, n_features = features.shape

        windows = np.empty(
            (n_frames, window_size, n_features),
            dtype=features.dtype,
        )

        for i in range(n_frames):
            windows[i] = padded[i : i + window_size]

        return windows[..., np.newaxis]

    def window_shape(self, n_features: int) -> tuple[int, int]:
        """
        Returns:
            (context_window, n_features)
        """
        return (2 * self.context_size + 1, n_features)
