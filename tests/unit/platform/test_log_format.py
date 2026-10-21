import json
import logging
import sys

from app.platform.log import JsonFormatter, configure_logging


def _record(**extra: object) -> logging.LogRecord:
    record = logging.LogRecord("app.request", logging.INFO, __file__, 1, "request", None, None)
    record.created = 1_760_000_000.123  # 2025-10-09T08:53:20.123Z
    for name, value in extra.items():
        setattr(record, name, value)
    return record


def test_request_record_is_one_json_line_with_all_fields() -> None:
    """AC-16: UTC time, level, method, path, status, duration and correlation id."""
    line = JsonFormatter().format(
        _record(correlation_id="c1", method="GET", path="/api/x", status=200, duration_ms=1.5)
    )
    assert "\n" not in line
    entry = json.loads(line)
    assert entry == {
        "time": "2025-10-09T08:53:20.123+00:00",
        "level": "INFO",
        "logger": "app.request",
        "message": "request",
        "correlation_id": "c1",
        "method": "GET",
        "path": "/api/x",
        "status": 200,
        "duration_ms": 1.5,
    }


def test_unknown_extra_fields_are_not_emitted() -> None:
    """Only whitelisted fields reach the log, so a stray extra cannot leak personal data."""
    entry = json.loads(JsonFormatter().format(_record(email="ali@example.com")))
    assert "email" not in entry
    assert "ali@example.com" not in json.dumps(entry)


def test_turkish_text_is_kept_readable() -> None:
    record = _record()
    record.msg = "İzin talebi işlendi"
    assert "İzin talebi işlendi" in JsonFormatter().format(record)


def test_exception_is_included() -> None:
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = _record()
        record.exc_info = sys.exc_info()
    entry = json.loads(JsonFormatter().format(record))
    assert "RuntimeError: boom" in entry["exception"]


def test_configure_logging_keeps_alembic_info_out_of_request_logs() -> None:
    """Review #3 / R-8: readiness reads the schema version through alembic, which logs at INFO."""
    root = logging.getLogger()
    alembic = logging.getLogger("alembic")
    saved = (root.handlers[:], root.level, alembic.level)
    try:
        configure_logging()
        assert alembic.getEffectiveLevel() == logging.WARNING
        assert not alembic.isEnabledFor(logging.INFO)
        assert logging.getLogger("app.request").isEnabledFor(logging.INFO)
    finally:
        root.handlers[:], root.level = saved[0], saved[1]
        alembic.setLevel(saved[2])
