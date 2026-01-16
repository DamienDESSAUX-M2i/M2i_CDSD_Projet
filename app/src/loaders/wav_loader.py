from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from src.loaders import AbstractLoader


class WAVLoader(AbstractLoader):
    """
    WAV file loader.
    Load audio data to a WAV file using the soundfile backend.
    """

    def load(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        file_path: Path,
        **kwargs: Any,
    ) -> None:
        """
        Load audio data to a WAV file.

        Args:
            audio_data (np.ndarray): Audio signal data. Shape must be (n_samples,) or (n_samples, n_channels).
            sample_rate (int): Sampling rate in Hz. Must be a positive integer.
            file_path (Path): Destination path of the WAV file. Must end with '.wav'.
            **kwargs: Additional keyword arguments forwarded to 'soundfile.write'.

        Raises:
            TypeError: If inputs are of invalid type.
            ValueError: If array dimension is invalid.
            ValueError: If the file path is invalid.
            RuntimeError: If writing the WAV file fails.
        """
        self._load_validate_inputs(
            audio_data=audio_data,
            sample_rate=sample_rate,
            file_path=file_path,
        )
        self._ensure_parent_directory(parent_directory_path=file_path.parent)

        try:
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
            self.logger.info(
                "WAV file successfully written",
                extra={
                    "path": str(file_path),
                },
            )
        except Exception as exc:
            self.logger.exception(
                "Failed to write WAV file",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("WAV writing failed") from exc

    def _load_validate_inputs(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        file_path: Path,
    ) -> None:
        """Raise an exception if an input is invalid."""
        if not isinstance(audio_data, np.ndarray):
            raise TypeError("audio_data must be a numpy ndarray.")
        if audio_data.ndim not in {1, 2}:
            raise ValueError("audio_data must be 1D (mono) or 2D (multi-channel).")
        if not isinstance(sample_rate, int) or sample_rate <= 0:
            raise TypeError("sample_rate must be a positive integer.")
        if not isinstance(file_path, Path):
            raise TypeError("file_path must be a pathlib.Path.")
        if not file_path.suffix.lower() == ".wav":
            raise ValueError("file_path must end with '.wav'.")
