from pathlib import Path


def validate_file_path(
    file_path: Path,
    suffix: str | None = None,
) -> None:
    """
    Validate an input archive file path.

    Args:
        file_path: Path to the archive file.
        suffix: Optional expected file extension.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is invalid.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    if (suffix is not None) and (file_path.suffix.lower() != suffix.lower()):
        raise ValueError(
            f"Invalid file extension: expected={suffix} received={file_path.suffix}"
        )
