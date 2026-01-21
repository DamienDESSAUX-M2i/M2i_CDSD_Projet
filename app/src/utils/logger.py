import logging
import os
from pathlib import Path

LOGGER_DIR_PATH = Path("./logs")  # /app/logs in container
LOGGER_NAME = os.getenv("LOGGER_NAME", "app")


def set_up_logger(
    name: str, logger_file_path: Path = None, level=logging.INFO
) -> logging.Logger:
    """Set up a logger.

    Args:
        name (str): Name of the logger.
        log_path (Path, optional): Path of the logger file. Defaults to None.
        level (_type_, optional): Level of the logger. Defaults to logging.INFO.

    Returns:
        logging.Logger: A configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "{asctime} - {levelname} - {module} - {funcName} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if logger_file_path:
        file_handler = logging.FileHandler(
            logger_file_path, mode="wt", encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def initialize_logger() -> bool:
    if not LOGGER_DIR_PATH.exists():
        LOGGER_DIR_PATH.mkdir(parents=True, exist_ok=True)

    set_up_logger(
        name=LOGGER_NAME, logger_file_path=LOGGER_DIR_PATH / f"{LOGGER_NAME}.log"
    )
