from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from src.extractors import AbstractExtractor


class ZipExtractor(AbstractExtractor):
    """Handles safe and atomic ZIP archive extraction."""

    def extract(self, archive: Path, output_dir: Path) -> None:
        """
        Extract a ZIP archive into a target directory in a safe and atomic way.

        The extraction is performed into a temporary directory to avoid partial writes.
        Once completed successfully, the temporary directory is moved to the final
        destination. Existing non-empty output directories are skipped to ensure
        idempotency.

        Security checks are performed to prevent Zip Slip attacks by validating that
        all extracted paths remain within the temporary directory.

        Args:
            archive: Path to the ZIP archive to extract.
            output_dir: Destination directory where files will be extracted.

        Raises:
            RuntimeError: If a Zip Slip attempt is detected.
            zipfile.BadZipFile: If the archive is not a valid ZIP file.
            OSError: If extraction or filesystem operations fail.
        """
        self.logger.info(
            f"Starting extraction, archive={str(archive)}, output_dir={str(output_dir)}"
        )

        if output_dir.exists():
            self.logger.info(
                f"Extraction skipped (directory already exists), output_dir={str(output_dir)}"
            )
            return

        tmp_dir = output_dir.parent / f"{output_dir.name}.tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        self.logger.debug(f"Temporary directory created, tmp_dir={str(tmp_dir)}")

        tmp_dir_resolved = tmp_dir.resolve()

        try:
            with zipfile.ZipFile(archive, "r") as z:
                members = z.infolist()

                self.logger.info(
                    f"Archive opened, archive={str(archive)}, num_files={len(members)}"
                )

                for member in members:
                    member_path = (tmp_dir / member.filename).resolve()

                    if not member_path.is_relative_to(tmp_dir_resolved):
                        self.logger.error(
                            f"Zip Slip detected, member={member.filename}"
                        )
                        raise RuntimeError("Zip Slip detected")

                    if member.is_dir():
                        member_path.mkdir(parents=True, exist_ok=True)
                    else:
                        member_path.parent.mkdir(parents=True, exist_ok=True)
                        with (
                            z.open(member) as source,
                            open(member_path, "wb") as target,
                        ):
                            shutil.copyfileobj(source, target)

                self.logger.debug(
                    f"Extraction to temporary directory completed, tmp_dir={str(tmp_dir)}"
                )

            shutil.move(tmp_dir, output_dir)

            self.logger.debug(
                f"Temporary directory moved to final destination, output_dir={str(output_dir)}"
            )

        except (zipfile.BadZipFile, OSError):
            self.logger.exception(f"Extraction failed, archive={str(archive)}")
            raise

        finally:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)
                self.logger.debug(
                    f"Temporary directory cleaned up, tmp_dir={str(tmp_dir)}"
                )

        self.logger.info(f"Extraction complete, output_dir={str(output_dir)}")
