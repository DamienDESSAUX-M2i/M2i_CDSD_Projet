import logging
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from src.utils import LOGGER_NAME


class WAVLoader:
    """
    WAV file writer utility.

    Responsible for validating and writing audio data to a WAV file using the soundfile backend.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(LOGGER_NAME)

    def load(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        file_path: Path,
        **kwargs: Any,
    ) -> None:
        """
        Write audio data to a WAV file.

        Args:
            audio_data (np.ndarray): Audio signal data. Shape must be (n_samples,) or (n_samples, n_channels).
            sample_rate (int): Sampling rate in Hz. Must be a positive integer.
            file_path (Path): Destination path of the WAV file.
            **kwargs: Additional keyword arguments forwarded to `soundfile.write` (e.g., subtype, format).

        Raises:
            ValueError: If inputs are invalid.
            RuntimeError: If writing the WAV file fails.
        """
        # Convert to Path and ensure .wav extension
        if not file_path.suffix.lower() == ".wav":
            file_path = file_path.with_suffix(".wav")

        self._validate_inputs(audio_data, sample_rate, file_path)

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            self.logger.info(
                "Writing WAV file",
                extra={
                    "path": str(file_path),
                    "sample_rate": sample_rate,
                    "shape": audio_data.shape,
                    "dtype": audio_data.dtype,
                },
            )

            sf.write(
                file=file_path,
                data=audio_data,
                samplerate=sample_rate,
                **kwargs,
            )

            self.logger.info(f"WAV file successfully written: {file_path}")

        except Exception as exc:
            self.logger.exception(f"Failed to write WAV file: {file_path}")
            raise RuntimeError("WAV writing failed") from exc

    @staticmethod
    def _validate_inputs(
        audio_data: np.ndarray,
        sample_rate: int,
        file_path: Path,
    ) -> None:
        if not isinstance(audio_data, np.ndarray):
            raise ValueError("audio_data must be a numpy ndarray.")

        if audio_data.ndim not in {1, 2}:
            raise ValueError("audio_data must be 1D (mono) or 2D (multi-channel).")

        if not isinstance(sample_rate, int) or sample_rate <= 0:
            raise ValueError("sample_rate must be a positive integer.")

        if not isinstance(file_path, Path):
            raise ValueError("file_path must be a pathlib.Path.")
