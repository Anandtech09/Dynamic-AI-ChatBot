"""
Structured logging configuration with request-aware context.
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from typing import Optional

# Context variable to track request IDs across async call stacks
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestFormatter(logging.Formatter):
    """Custom formatter that includes request_id in every log line."""

    def format(self, record: logging.LogRecord) -> str:
        record.request_id = request_id_var.get("")
        return super().format(record)


def setup_logging(level: str = "INFO", log_file: Optional[str] = "logs/app.log") -> None:
    """Configure structured logging for stdout and rotating file output."""
    fmt = (
        "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s"
    )
    formatter = RequestFormatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.handlers.clear()

    # Console / Docker stdout stream
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # Persistent log file with rotation
    if log_file:
        try:
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning("Could not initialize file log handler: %s", e)

    # Quiet noisy third-party loggers
    for noisy in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def generate_request_id() -> str:
    return uuid.uuid4().hex[:12]
