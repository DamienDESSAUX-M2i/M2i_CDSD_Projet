import logging
from pathlib import Path


def setup_logger(name: str, path: Path = None, level=logging.INFO) -> logging.Logger:
    """Set up a logger.

    Args:
        name (str): Name of the logger.
        log_path (Path, optional): Path of the logger file. Defaults to None.
        level (_type_, optional): Level of the logger. Defaults to logging.INFO.

    Returns:
        logging.Logger: A configurated logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "{asctime} - {name} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if path:
        file_handler = logging.FileHandler(path, mode="wt", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
