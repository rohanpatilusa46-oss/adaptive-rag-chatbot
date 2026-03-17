from __future__ import annotations

import logging
import sys
from typing import Any, Dict

import structlog

from app.core.config import settings


def _get_log_level() -> int:
    level_name = settings.log_level.upper()
    return getattr(logging, level_name, logging.INFO)


def configure_logging() -> None:
    """Configure standard library logging and structlog for structured logs."""
    logging.basicConfig(
        level=_get_log_level(),
        format="%(message)s",
        stream=sys.stdout,
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


def bind_request_context(logger: structlog.stdlib.BoundLogger, **kwargs: Dict[str, Any]) -> structlog.stdlib.BoundLogger:
    """Bind contextual information (e.g., request_id, user_id) to a logger."""
    return logger.bind(**kwargs)

