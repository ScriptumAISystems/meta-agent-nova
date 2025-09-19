"""Logging utilities for Nova monitoring.

Provides basic logging functionality for the Nova monitoring module.
"""

import logging

# Create a logger for the Nova monitoring module
logger = logging.getLogger("nova.monitoring")

# Configure default handler if no handlers are present (e.g. when imported directly)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def configure_logger(level: int = logging.INFO) -> None:
    """Configure the Nova monitoring logger's level.

    Args:
        level: Logging level to set.
    """
    logger.setLevel(level)


def log_info(message: str) -> None:
    """Log an informational message."""
    logger.info(message)


def log_warning(message: str) -> None:
    """Log a warning message."""
    logger.warning(message)


def log_error(message: str) -> None:
    """Log an error message."""
    logger.error(message)
