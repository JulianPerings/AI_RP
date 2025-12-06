"""Logging configuration using Loguru."""

import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    """Configure application logging."""
    # Remove default handler
    logger.remove()

    # Add custom handler with formatting
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
    )

    # Add file handler for production
    if settings.is_production:
        logger.add(
            "logs/app_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="30 days",
            level="INFO",
            format=log_format,
            colorize=False,
        )

    return logger


# Initialize logger
log = setup_logging()
