import logging
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from src.utils import LOGGER_NAME


class WAVExtractor:
    """
    WAV file reader utility.

    Responsible for loading audio data and metadata from a WAV file using the soundfile backend.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(LOGGER_NAME)

    def extract(
        self,
        file_path: Path,
        **kwargs: Any,
    ) -> tuple[np.ndarray, int]:
        """
        Extract audio data and sample rate from a WAV file.

        Args:
            file_path (Path): Path to the WAV file.
            **kwargs: Additional keyword arguments forwarded to `soundfile.read` (e.g., dtype, always_2d).

        Returns:
            tuple[np.ndarray, int]: A tuple containing audio_data, a numpy array of shape (n_samples,) or (n_samples, n_channels), and sample_rate, a sampling rate in Hz.

        Raises:
            FileNotFoundError: If the WAV file does not exist.
            ValueError: If inputs are invalid.
            RuntimeError: If reading the WAV file fails.
        """
        self._validate_inputs(file_path)

        try:
            self.logger.info(
                "Reading WAV file",
                extra={
                    "path": str(file_path),
                },
            )

            audio_data, sample_rate = sf.read(
                file=file_path,
                **kwargs,
            )

            self.logger.info(
                "WAV extraction completed",
                extra={
                    "path": str(file_path),
                    "sample_rate": sample_rate,
                    "shape": audio_data.shape,
                    "dtype": audio_data.dtype,
                },
            )

            return audio_data, sample_rate

        except Exception as exc:
            self.logger.exception(f"Failed to extract WAV file: {file_path}")
            raise RuntimeError("WAV extraction failed") from exc

    @staticmethod
    def _validate_inputs(file_path: Path) -> None:
        if not isinstance(file_path, Path):
            raise ValueError("file_path must be a pathlib.Path.")

        if not file_path.exists():
            raise FileNotFoundError(f"WAV file not found: {file_path}")

        if file_path.suffix.lower() != ".wav":
            raise ValueError(
                f"Invalid file extension '{file_path.suffix}'. Expected '.wav'."
            )
