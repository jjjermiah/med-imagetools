# logging_config.py
import sys

from loguru import logger


def setup_logger(level: str) -> None:
    # Remove the default handler to reset configuration
    logger.remove()
    # Add a new handler with the passed log level
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level:^8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        level=level.upper(),  # Use the dynamic log level here
    )
