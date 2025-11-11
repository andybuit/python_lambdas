"""Centralized logging configuration using AWS Lambda Powertools."""

from typing import Any

from aws_lambda_powertools import Logger

# Create a logger instance for the service
logger = Logger(service="psn-emulator")


def get_logger(name: str) -> Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: The name of the module requesting the logger

    Returns:
        Logger: Configured logger instance
    """
    return Logger(service="psn-emulator", name=name)


def log_lambda_event(event: dict[str, Any], context: Any) -> None:
    """
    Log Lambda event details for debugging.

    Args:
        event: The Lambda event dict
        context: The Lambda context object
    """
    logger.info(
        "Lambda invocation",
        extra={
            "request_id": context.request_id if context else None,
            "function_name": context.function_name if context else None,
            "event": event,
        },
    )
