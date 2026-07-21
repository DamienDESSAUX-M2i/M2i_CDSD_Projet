import logging

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class ContextWindowBuilder:
    """Build temporal context windows for convolutional audio models.

    The builder transforms frame-wise feature matrices into overlapping
    temporal windows suitable for CNN/RCNN architectures.

    Input shape:

        (n_frames, n_features)

    Output shape:

        (n_frames, context_window, n_features, 1)

    The last dimension represents the single input channel expected by
    convolutional neural network layers.

    Attributes:
        context_size:
            Number of frames added before and after the current frame.
            The resulting temporal dimension is:
            ``2 * context_size + 1``.
    """

    def __init__(
        self,
        context_size: int,
    ) -> None:
        """Initialize the context window builder.

        Args:
            context_size:
                Number of contextual frames added on each side.

        Raises:
            ValueError:
                If context_size is negative.
        """
        if context_size < 0:
            raise ValueError("context_size must be greater than or equal to zero.")

        self._context_size = context_size

    @property
    def context_window_size(self) -> int:
        """Return the temporal size of each context window.

        Returns:
            Number of frames contained in one temporal window.
        """
        return 2 * self._context_size + 1

    def build_context_windows(
        self,
        features: NDArray[np.float32],
    ) -> NDArray[np.float32]:
        """Construct temporal context windows.

        Edge padding is applied to preserve the number of frames.
        The current frame is centered inside each temporal window.

        Args:
            features:
                Feature matrix with shape:

                ``(n_frames, n_features)``

        Returns:
            Contextual feature tensor with shape:

            ``(n_frames, context_window, n_features, 1)``

        Raises:
            ValueError:
                If the input feature matrix is empty or has an invalid shape.
        """

        if features.size == 0:
            raise ValueError("Input features array cannot be empty.")

        if features.ndim != 2:
            raise ValueError(
                "Expected features with shape "
                "(n_frames, n_features), "
                f"got {features.shape}."
            )

        logger.debug(
            ("Building context windows: frames=%d, features=%d, context=%d."),
            features.shape[0],
            features.shape[1],
            self._context_size,
        )

        padding = self._context_size

        padded_features = np.pad(
            features,
            pad_width=(
                (padding, padding),
                (0, 0),
            ),
            mode="edge",
        )

        n_frames, n_features = features.shape

        windows = np.empty(
            (
                n_frames,
                self.context_window_size,
                n_features,
            ),
            dtype=np.float32,
        )

        for index in range(n_frames):
            windows[index] = padded_features[index : index + self.context_window_size]

        output = windows[..., np.newaxis]

        logger.debug(
            "Context windows generated: output_shape=%s.",
            output.shape,
        )

        return output

    def window_shape(
        self,
        n_features: int,
    ) -> tuple[int, int, int]:
        """Return the model input window shape.

        Args:
            n_features:
                Number of extracted audio features.

        Returns:
            Tuple containing:

            ``(context_window, n_features, channels)``

        Example:
            For ``context_size=5`` and ``n_features=256``:

            ``(11, 256, 1)``
        """
        return (2 * self.context_window_size + 1, n_features, 1)
