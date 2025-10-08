"""Centralized logging configuration for Nova."""
from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Optional

_DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def initialize_logging(
    *,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
) -> None:
    """Initialise structured logging for all Nova components."""
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    }
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file,
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "standard",
        }

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": _DEFAULT_FORMAT,
                    "datefmt": _DEFAULT_DATE_FORMAT,
                }
            },
            "handlers": handlers,
            "root": {
                "level": log_level,
                "handlers": list(handlers.keys()),
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured via :func:`initialize_logging`."""
    return logging.getLogger(name)


__all__ = ["initialize_logging", "get_logger"]
