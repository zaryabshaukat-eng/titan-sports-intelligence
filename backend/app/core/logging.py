"""Structured JSON logging with request correlation support."""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    """Serialize log records into compact, machine-readable JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Build a stable log event without serializing sensitive process state."""
        event: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = request_id_context.get()
        if request_id:
            event["request_id"] = request_id

        extra_fields = getattr(record, "extra_fields", None)
        if isinstance(extra_fields, dict):
            event.update(extra_fields)

        if record.exc_info:
            event["exception"] = self.formatException(record.exc_info)

        return json.dumps(event, default=str, separators=(",", ":"))


def configure_logging(log_level: str) -> None:
    """Configure a single JSON stdout handler for application logs."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = True


def get_logger(name: str) -> logging.Logger:
    """Return a named standard-library logger configured by `configure_logging`."""
    return logging.getLogger(name)
