"""
Central logging configuration for AICMO.

Provides structured logging setup with consistent formatting across all modules.
Enables aggregation and analysis of errors/warnings in production.
"""

import logging
import sys
from typing import Optional

# Standard logger names for different subsystems
LOGGER_EXPORT = "aicmo.export"
LOGGER_VALIDATION = "aicmo.quality"
LOGGER_LEARNING = "aicmo.learning"
LOGGER_LLM = "aicmo.llm"
LOGGER_MAIN = "aicmo.main"


def configure_logging(level: str = "INFO") -> None:
    """
    Configure structured logging for all AICMO modules.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Design: Call once at application startup. Sets up handlers, formatters,
    and log levels for all AICMO modules.
    """
    # Parse level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels, filter at handler

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Structured formatter: timestamp | level | logger_name | message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stderr for errors/warnings, stdout for info/debug)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set level for specific AICMO loggers
    for logger_name in [
        LOGGER_EXPORT,
        LOGGER_VALIDATION,
        LOGGER_LEARNING,
        LOGGER_LLM,
        LOGGER_MAIN,
    ]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ in calling module)

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Operation complete")
    """
    return logging.getLogger(name)


class StructuredLogContext:
    """
    Context manager for structured logging with additional fields.

    Allows adding contextual data (e.g., report_id, user_id) to log messages
    without modifying every log call.

    Example:
        with StructuredLogContext(report_id="abc123"):
            logger.info("Processing report")  # Logged with report_id attached
    """

    def __init__(self, **context_fields):
        """Initialize with context fields."""
        self.context = context_fields
        self.logger = logging.getLogger(LOGGER_MAIN)

    def __enter__(self):
        """Enter context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        pass

    def log(self, level: str, message: str, **extra_fields) -> None:
        """
        Log with context fields.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: Log message
            **extra_fields: Additional fields to include
        """
        combined_fields = {**self.context, **extra_fields}
        field_str = " | ".join(f"{k}={v}" for k, v in combined_fields.items())
        full_message = f"{message} | {field_str}" if field_str else message

        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(full_message)


# Convenience functions for common log operations
def log_validation_complete(
    issue_count: int,
    error_count: int,
    warning_count: int,
    report_name: Optional[str] = None,
) -> None:
    """Log completion of report validation."""
    logger = get_logger(LOGGER_VALIDATION)
    msg = f"Validation complete: {issue_count} issue(s) ({error_count} error, {warning_count} warning)"
    if report_name:
        msg += f" | report={report_name}"
    logger.info(msg)


def log_validation_blocked(reason: str, section: Optional[str] = None) -> None:
    """Log when validation blocks an export."""
    logger = get_logger(LOGGER_VALIDATION)
    msg = f"Validation blocked export: {reason}"
    if section:
        msg += f" | section={section}"
    logger.warning(msg)


def log_export_success(export_type: str, size_bytes: int) -> None:
    """Log successful export."""
    logger = get_logger(LOGGER_EXPORT)
    logger.info(f"{export_type.upper()} export successful | size={size_bytes} bytes")


def log_export_failure(export_type: str, error_msg: str, exc_info: bool = False) -> None:
    """Log export failure."""
    logger = get_logger(LOGGER_EXPORT)
    logger.error(
        f"{export_type.upper()} export failed: {error_msg}",
        exc_info=exc_info,
    )


def log_learning_event(
    event_type: str, source: str, section_count: int, success: bool = True
) -> None:
    """Log Phase L learning event."""
    logger = get_logger(LOGGER_LEARNING)
    status = "success" if success else "failed"
    logger.info(f"Learning {event_type} ({status}) | source={source} | sections={section_count}")


def log_llm_call(model: str, prompt_tokens: int, completion_tokens: int, latency_ms: float) -> None:
    """Log LLM API call."""
    logger = get_logger(LOGGER_LLM)
    total = prompt_tokens + completion_tokens
    logger.info(
        f"LLM call | model={model} | tokens={total} "
        f"(prompt={prompt_tokens}, completion={completion_tokens}) | latency={latency_ms:.0f}ms"
    )


def log_llm_error(model: str, error_msg: str) -> None:
    """Log LLM API error."""
    logger = get_logger(LOGGER_LLM)
    logger.error(f"LLM error | model={model} | {error_msg}")
