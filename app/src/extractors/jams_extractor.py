from pathlib import Path
from typing import Any

import jams

from src.extractors import AbstractExtractor


class JAMSExtractor(AbstractExtractor):
    """
    JAMS file extractor.
    Extract data from a JAMS file using jams backend.
    """

    def extract(self, file_path: Path, **kwargs: Any) -> jams.JAMS:
        """Extract data from a JAMS file.

        Args:
            file_path (Path): Path of the JAMS file. Must end with '.jams'.
            **kwargs: Additional keyword arguments forwarded to 'jams.load'.

        Raises:
            FileNotFoundError: If the JAMS file does not exist.
            ValueError: If inputs are invalid.
            RuntimeError: If reading the JAMS file fails.

        Returns:
            jams.JAMS: jams.JAMS extract from the JAMS file.
        """
        self._validate_file_path(file_path=file_path, suffix=".jams")

        try:
            self.logger.info(
                "Reading JAMS file",
                extra={
                    "path": str(file_path),
                },
            )
            jam = jams.load(path_or_file=str(file_path), **kwargs)
            self.logger.info(
                "JAMS extraction completed",
                extra={
                    "path": str(file_path),
                    "metadata": jam.file_metadata,
                },
            )
            return jam
        except Exception as exc:
            self.logger.exception(
                "Failed to load JAMS file.",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("JAMS extraction failed") from exc
