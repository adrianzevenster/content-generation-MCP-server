"""
Structured logging configuration for production observability.

Uses structlog for structured logging with JSON formatting.
Provides consistent logging across all services.
"""
import os
import logging
import structlog
from pythonjsonlogger import jsonlogger


def configure_logging():
    """
    Configure structured logging for the application.

    Logs are output in JSON format for easy parsing by log aggregation systems.
    Log level can be controlled via LOG_LEVEL environment variable (default: INFO).
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure standard library logging first
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level, logging.INFO),
    )

    # Configure JSON formatter for production
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
    )
    handler.setFormatter(formatter)

    # Get root logger and configure it
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Configure structlog for structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """
    Get a structured logger instance.

    Usage:
        logger = get_logger(__name__)
        logger.info("user_action", user_id="123", action="login")
        logger.error("database_error", error=str(e), query=query, exc_info=True)

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        A structlog BoundLogger instance
    """
    return structlog.get_logger(name)
