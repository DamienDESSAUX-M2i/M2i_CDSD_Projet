from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from src.extractors import AbstractExtractor
from src.utils import validate_file_path


class WAVExtractor(AbstractExtractor):
    """
    WAV file extractor.
    Extract audio data and sample rate from a WAV file using the soundfile backend.
    """

    def extract(self, file_path: Path, **kwargs: Any) -> tuple[np.ndarray, int]:
        """
        Extract audio data and sample rate from a WAV file.

        Args:
            file_path (Path): Path to the WAV file. Must end with '.wav'.
            **kwargs: Additional keyword arguments forwarded to 'soundfile.read'.

        Returns:
            tuple[np.ndarray, int]: A tuple containing audio_data, a numpy array of shape (n_samples,) or (n_samples, n_channels), and sample_rate, a sampling rate in Hz.

        Raises:
            FileNotFoundError: If the WAV file does not exist.
            ValueError: If inputs are invalid.
            RuntimeError: If reading the WAV file fails.
        """
        validate_file_path(file_path=file_path, suffix=".wav")

        try:
            self.logger.debug(
                f"Reading WAV file: path={str(file_path)}",
            )
            audio_data, sample_rate = sf.read(
                file=file_path,
                **kwargs,
            )
            self.logger.debug(
                f"WAV extraction completed: "
                f"path={str(file_path)}, "
                f"sample_rate={sample_rate}, "
                f"shape={audio_data.shape}, "
                f"dtype={audio_data.dtype}"
            )
            return audio_data, sample_rate
        except Exception as exception:
            self.logger.exception(
                f"Failed to load WAV file: path={str(file_path)}",
            )
            raise RuntimeError("WAV extraction failed") from exception
