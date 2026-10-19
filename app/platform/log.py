"""JSON log lines on stdout (spec 0001 R-8): one object per line, UTC time, no personal data."""

import json
import logging
import sys
from datetime import UTC, datetime

# Extra fields a record may carry (logger.info(..., extra={...})); anything else is not emitted.
STRUCTURED_FIELDS = ("correlation_id", "method", "path", "status", "duration_ms")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "time": datetime.fromtimestamp(record.created, tz=UTC).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for name in STRUCTURED_FIELDS:
            if hasattr(record, name):
                entry[name] = getattr(record, name)
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def configure_logging() -> None:
    """Route every logger (uvicorn included) through one JSON handler on stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
