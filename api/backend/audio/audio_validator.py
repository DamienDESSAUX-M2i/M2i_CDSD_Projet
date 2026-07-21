from typing import Any

import numpy as np
from numpy.typing import NDArray


def validate_audio(
    audio_data: NDArray[np.floating[Any]],
) -> None:
    """Validate audio tensor integrity.

    The validator ensures that audio tensors are suitable for DSP
    processing.

    Accepted shapes:

        - ``(n_samples,)`` for mono audio.
        - ``(n_channels, n_samples)`` for multi-channel audio before
          mono conversion.

    Args:
        audio_data:
            Audio waveform tensor.

    Raises:
        TypeError:
            If the audio dtype is not floating point.

        ValueError:
            If the tensor shape is invalid, empty, or contains
            non-finite values.
    """

    if audio_data.size == 0:
        raise ValueError("Audio data cannot be empty.")

    if audio_data.ndim not in (1, 2):
        raise ValueError(
            (
                "Audio data must have shape "
                "(n_samples,) or (n_channels, n_samples). "
                f"Received shape={audio_data.shape}."
            ),
        )

    if not np.issubdtype(
        audio_data.dtype,
        np.floating,
    ):
        raise TypeError(
            (
                "Audio data must use a floating-point dtype. "
                f"Received dtype={audio_data.dtype}."
            ),
        )

    if not np.isfinite(audio_data).all():
        raise ValueError("Audio data contains NaN or infinite values.")
