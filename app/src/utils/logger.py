from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_DIR_PATH = Path("./app/logs")
LOGGER_NAME = "app"
LOG_FORMAT = "{asctime} | {levelname:<8} | {name} | {module}: {funcName} | {message}"


def _ensure_log_directory(path: Path) -> None:
    """
    Ensure that the log directory exists.

    Args:
        path: Directory path to create if missing.
    """

    path.mkdir(parents=True, exist_ok=True)


def _build_formatter() -> logging.Formatter:
    """
    Create a shared log formatter.

    Returns:
        Configured logging formatter using structured format.
    """

    return logging.Formatter(
        LOG_FORMAT,
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _set_up_logger(
    name: str,
    logger_file_path: Path | None = None,
    level: int = logging.DEBUG,
    *,
    propagate: bool = False,
    force_reset: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger instance.

    This function is idempotent when `force_reset=True`: it clears existing
    handlers to avoid duplicate logs.

    Args:
        name: Logger name.
        logger_file_path: Optional file path for rotating file logging.
        level: Minimum logging level for the logger.
        propagate: Whether to propagate logs to parent loggers.
        force_reset: If True, remove existing handlers before configuration.

    Returns:
        Configured logging.Logger instance.
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = propagate

    if force_reset:
        logger.handlers.clear()

    formatter = _build_formatter()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if logger_file_path is not None:
        file_handler = RotatingFileHandler(
            logger_file_path,
            mode="a",
            maxBytes=5_242_880,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def initialize_logger() -> logging.Logger:
    """
    Initialize application logger with default configuration.

    Ensures log directory exists and sets up a rotating file logger
    alongside console logging.

    Returns:
        Configured root application logger.
    """

    _ensure_log_directory(LOGGER_DIR_PATH)

    return _set_up_logger(
        name=LOGGER_NAME,
        logger_file_path=LOGGER_DIR_PATH / f"{LOGGER_NAME}.log",
    )


def get_logger() -> logging.Logger:
    """
    Retrieve the preconfigured application logger.

    This function assumes that `initialize_logger()` has already been
    called during application startup. It does not modify logger state.

    Returns:
        The application logger instance identified by LOGGER_NAME.
    """

    return logging.getLogger(LOGGER_NAME)
