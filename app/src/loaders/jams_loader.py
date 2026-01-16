from pathlib import Path
from typing import Any

import jams

from src.loaders import AbstractLoader


class JAMSLoader(AbstractLoader):
    """
    JAMS file loader.
    Load a jams.JAMS object to a JAMS file.
    """

    def load(self, jam: jams.JAMS, file_path: Path, **kwargs: Any) -> None:
        """Load a jams.JAMS object to a JAMS file.

        Args:
            jam (jams.JAMS): JAMS object to load.
            file_path (Path): Destination path of the JAMS file.
            **kwargs: Additional keyword arguments forwarded to 'jams.dumps'.

        Raises:
            TypeError: If inputs are of invalid type.
            ValueError: If the file path is invalid.
            RuntimeError: If writing the JAMS file fails.
        """
        self._validate_inputs(jam=jam, file_path=file_path)
        self._ensure_parent_directory(parent_dir=file_path.parent)

        try:
            self.logger.info(
                "Loading JAMS file",
                extra={
                    "path": str(file_path),
                },
            )
            file_path.write_text(jam.dumps(**kwargs), encoding="utf-8")
            self.logger.info(
                "JAMS file saved successfully",
                extra={
                    "path": str(file_path),
                },
            )
        except Exception as e:
            self.logger.error(
                "Failed to save JAMS file",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("JAMS Loader failed") from e

    def _validate_inputs(self, jam: jams.JAMS, file_path: Path) -> None:
        """Raise an exception if an input is invalid."""
        if not isinstance(jam, jams.JAMS):
            raise TypeError(
                f"'jam' must be a jams.JAMS instance, got {type(jam).__name__}"
            )

        if not isinstance(file_path, Path):
            raise TypeError(
                f"'file_path' must be a pathlib.Path, got {type(file_path).__name__}"
            )

        if file_path.suffix.lower() != ".jams":
            raise ValueError(
                f"Invalid file extension '{file_path.suffix}', expected '.jams'"
            )
