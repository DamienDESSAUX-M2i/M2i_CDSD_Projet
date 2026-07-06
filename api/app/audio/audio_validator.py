import numpy as np

from .audio_type import FloatAudioArray


def validate_audio(audio_data: FloatAudioArray) -> None:
    """Validate audio tensor integrity.

    Args:
        audio_data: Audio signal to validate.

    Raises:
        TypeError: If the dtype is not floating-point.
        ValueError: If the audio shape or values are invalid.
    """

    if audio_data.size == 0:
        raise ValueError("Audio data cannot be empty.")

    if audio_data.ndim not in (1, 2):
        raise ValueError(
            "Audio data must have shape (n_samples,) or (n_channels, n_samples)."
        )

    if not np.issubdtype(audio_data.dtype, np.floating):
        raise TypeError("Audio data must use a floating-point dtype.")

    if not np.isfinite(audio_data).all():
        raise ValueError("Audio data contains NaN or infinite values.")
