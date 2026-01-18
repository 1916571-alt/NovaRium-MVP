"""
Centralized logging configuration for NovaRium Edu.

Usage:
    from src.core.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Message")
"""
import logging
import logging.handlers
import os
import sys
from typing import Optional


# =============================================================================
# Configuration
# =============================================================================

# Log levels
LOG_LEVEL = os.getenv("NOVARIUM_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# File logging (optional)
LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "logs"
)
LOG_FILE = os.path.join(LOG_DIR, "novarium.log")
LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_FILE_BACKUP_COUNT = 5

# Whether to enable file logging
ENABLE_FILE_LOGGING = os.getenv("NOVARIUM_LOG_TO_FILE", "false").lower() == "true"


# =============================================================================
# Logger Setup
# =============================================================================

_configured = False


def _setup_logging() -> None:
    """Configure root logger with handlers."""
    global _configured

    if _configured:
        return

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(LOG_LEVEL)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if ENABLE_FILE_LOGGING:
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                LOG_FILE,
                maxBytes=LOG_FILE_MAX_BYTES,
                backupCount=LOG_FILE_BACKUP_COUNT,
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(LOG_LEVEL)
            root_logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            console_handler.stream.write(
                f"[WARNING] Could not enable file logging: {e}\n"
            )

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing started")
        logger.error("An error occurred", exc_info=True)
    """
    _setup_logging()
    return logging.getLogger(name)


# =============================================================================
# Convenience Functions
# =============================================================================

def log_exception(logger: logging.Logger, message: str, exc: Exception) -> None:
    """
    Log an exception with traceback.

    Args:
        logger: Logger instance
        message: Context message
        exc: Exception instance
    """
    logger.error(f"{message}: {type(exc).__name__}: {exc}", exc_info=True)


def log_api_call(
    logger: logging.Logger,
    method: str,
    url: str,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None
) -> None:
    """
    Log an API call with consistent format.

    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        error: Error message if request failed
    """
    parts = [f"{method} {url}"]

    if status_code is not None:
        parts.append(f"status={status_code}")

    if duration_ms is not None:
        parts.append(f"duration={duration_ms:.0f}ms")

    if error:
        parts.append(f"error={error}")
        logger.error(" | ".join(parts))
    else:
        logger.info(" | ".join(parts))


def log_db_query(
    logger: logging.Logger,
    query: str,
    duration_ms: Optional[float] = None,
    rows_affected: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """
    Log a database query with consistent format.

    Args:
        logger: Logger instance
        query: SQL query (will be truncated)
        duration_ms: Query duration in milliseconds
        rows_affected: Number of rows affected/returned
        error: Error message if query failed
    """
    # Truncate long queries
    query_preview = query[:100].replace("\n", " ").strip()
    if len(query) > 100:
        query_preview += "..."

    parts = [f"SQL: {query_preview}"]

    if duration_ms is not None:
        parts.append(f"duration={duration_ms:.0f}ms")

    if rows_affected is not None:
        parts.append(f"rows={rows_affected}")

    if error:
        parts.append(f"error={error}")
        logger.error(" | ".join(parts))
    else:
        logger.debug(" | ".join(parts))


# =============================================================================
# Context Manager for Timed Operations
# =============================================================================

class LogTimer:
    """
    Context manager for timing and logging operations.

    Example:
        with LogTimer(logger, "Data processing"):
            process_data()
        # Logs: "Data processing completed in 1234ms"
    """

    def __init__(self, logger: logging.Logger, operation: str, level: int = logging.INFO):
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time: Optional[float] = None

    def __enter__(self) -> "LogTimer":
        import time
        self.start_time = time.time()
        self.logger.log(self.level, f"{self.operation} started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        import time
        duration_ms = (time.time() - self.start_time) * 1000

        if exc_type is not None:
            self.logger.error(
                f"{self.operation} failed after {duration_ms:.0f}ms: {exc_val}"
            )
        else:
            self.logger.log(
                self.level,
                f"{self.operation} completed in {duration_ms:.0f}ms"
            )
