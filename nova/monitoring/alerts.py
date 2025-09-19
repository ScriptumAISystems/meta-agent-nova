"""
Alerting utilities for Nova monitoring.

This module provides basic alert notification functionalities for the Nova monitoring system.
Future integrations might include Slack, email, or other communication platforms.
"""

import logging

# Use the existing Nova monitoring logger
from .logging import logger

def send_alert(severity: str, message: str) -> None:
    """
    Send an alert with a given severity level.

    Args:
        severity: The severity level of the alert (e.g. "info", "warning", "critical").
        message: The alert message to send.
    """
    if severity.lower() == "critical":
        logger.critical(message)
    elif severity.lower() == "warning":
        logger.warning(message)
    else:
        logger.info(message)


def notify_critical(message: str) -> None:
    """
    Notify about a critical issue.

    Args:
        message: Description of the critical issue.
    """
    send_alert("critical", message)


def notify_warning(message: str) -> None:
    """
    Notify about a warning issue.

    Args:
        message: Description of the warning.
    """
    send_alert("warning", message)


def notify_info(message: str) -> None:
    """
    Notify about an informational message.

    Args:
        message: Description of the informational message.
    """
    send_alert("info", message)
