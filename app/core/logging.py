import logging
import os
import sys
from typing import Any, Dict, Union

from loguru import logger

from app.core.config import settings
from app.core.context import request_id_context


class InterceptHandler(logging.Handler):
    """
    Custom logging handler to intercept standard Python logging records
    (from Uvicorn, FastAPI, SQLAlchemy, etc.) and redirect them to Loguru.

    This ensures that logs from all libraries follow the same format,
    rotation, and asynchronous writing rules defined in Loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level: Union[str, int] = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated.
        # We skip frames belonging to the 'logging' module to ensure the log
        # correctly shows the actual file and line number of the source code.
        frame, depth = logging.currentframe(), 2
        while frame and (
                frame.f_code.co_filename == logging.__file__
                or "logging" in frame.f_code.co_filename
        ):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def patch_record(record: Dict[str, Any]) -> None:
    """
    Loguru patcher that bridges the asynchronous ContextVar (request_id)
    into every log record. This allows us to track all logs belonging
    to a specific request across the entire application stack.
    """
    rid = request_id_context.get()

    # Defaults to 'SYSTEM' for logs generated outside of a request lifecycle
    # (e.g., during application startup or background tasks).
    record["extra"]["request_id"] = rid if rid else "SYSTEM"


def setup_logging() -> None:
    """
    Configures the global logging system for the FastAPI application.
    Optimized for Dockerized VPS deployment using persistent volumes.
    """

    # 1. Ensure the log directory exists on the VPS host/volume
    os.makedirs(settings.log_dir, exist_ok=True)

    # 2. Configure Loguru with our context patcher for Request ID tracking
    logger.configure(patcher=patch_record)

    # 3. Wipe Loguru's default handlers to prevent duplicate/unformatted stdout
    logger.remove()

    # 4. Define Log Formats
    # Console: Colorized for high readability in 'docker logs' or terminal
    # File: Clean text without ANSI colors for efficient 'grep' and historical analysis
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<magenta>{extra[request_id]}</magenta> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
        "{extra[request_id]} | {name}:{function}:{line} - {message}"
    )

    # 5. Sink: Standard Output (Internal Docker/Console stream)
    logger.add(
        sys.stdout,
        format=console_format,
        enqueue=True,  # ASYNC: moves log processing to a background thread
        level=settings.log_level
    )

    # 6. Sink: Persistent File (VPS Disk)
    # - rotation: Daily at midnight (defined in .env)
    # - retention: Automatically deletes logs older than 15 days
    # - compression: Zips old logs to save significant VPS disk space
    logger.add(
        os.path.join(settings.log_dir, "app.log"),
        format=file_format,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",
        enqueue=True,  # ASYNC: Disk I/O will not block API response time
        level=settings.log_level
    )

    # 7. Hijack and Force-Format Stubborn Standard Libraries
    # We clear all existing handlers from these specific loggers so they
    # stop printing raw, unformatted text and use our InterceptHandler instead.
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Specifically targeted loggers that often bypass standard configurations
    stubborn_loggers = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "starlette",
        "httpx"
    ]

    for name in stubborn_loggers:
        _logger = logging.getLogger(name)

        # Remove all existing handlers to prevent duplicate raw console output
        for handler in _logger.handlers[:]:
            _logger.removeHandler(handler)
        _logger.handlers = []

        # Force logs to propagate up to our root InterceptHandler
        _logger.propagate = True
        _logger.setLevel(logging.getLevelName(settings.log_level.upper()))
