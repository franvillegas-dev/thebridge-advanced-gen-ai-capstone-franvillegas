import json
import logging
import os
import sys
from typing import Any

DEFAULT_LOG_LEVEL = os.getenv("AGILE_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("AGILE_LOG_FORMAT", "text").lower()


class _JsonFormatter(logging.Formatter):
    """Formatter that emits structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key in ("agent", "tool", "session_id", "correlation_id"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, default=str, ensure_ascii=False)


class _TextFormatter(logging.Formatter):
    """Human-readable formatter with key context fields."""

    def format(self, record: logging.LogRecord) -> str:
        extras = []
        for key in ("agent", "tool", "session_id", "correlation_id"):
            value = getattr(record, key, None)
            if value is not None:
                extras.append(f"{key}={value}")
        prefix = " ".join(extras)
        if prefix:
            record.msg = f"[{prefix}] {record.msg}"
        return super().format(record)


def configure_logging(level: str | None = None) -> None:
    """Configure root logging for the Agile Agent backend.

    Reads AGILE_LOG_LEVEL (default INFO) and AGILE_LOG_FORMAT (text|json).
    """
    effective_level = (level or DEFAULT_LOG_LEVEL).upper()
    if LOG_FORMAT == "json":
        formatter: logging.Formatter = _JsonFormatter()
    else:
        formatter = _TextFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(effective_level)
    # Avoid duplicate handlers if configure_logging is called more than once.
    root.handlers = [handler]

    # Reduce noise from third-party libraries while keeping our own logs visible.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a logger with the given name."""
    return logging.getLogger(name)


def log_extra(**kwargs: Any) -> dict[str, Any]:
    """Build extra kwargs for logging.Logger calls to include structured context."""
    return {"extra": kwargs}
