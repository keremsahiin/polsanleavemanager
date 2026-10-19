import logging
import re
from pathlib import Path

import pytest

from app.platform.log import JsonFormatter
from tests.conftest import running_app


def _request_records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == "app.request"]


def _server_records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    """Records the application writes; the test client (httpx) logs its own request URL."""
    return [r for r in caplog.records if r.name.split(".")[0] in {"app", "uvicorn"}]


def test_one_json_line_per_request_with_fields(
    migrated_database: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-16: every response has the id header; one log record per request carries it."""
    caplog.set_level(logging.INFO)
    with running_app(migrated_database) as client:
        responses = [client.get("/api/health/live"), client.get("/api/nope")]
    records = _request_records(caplog)
    assert len(records) == len(responses)
    for response, record in zip(responses, records, strict=True):
        assert record.correlation_id == response.headers["x-request-id"]  # type: ignore[attr-defined]
        assert record.status == response.status_code  # type: ignore[attr-defined]
        assert record.method == "GET"  # type: ignore[attr-defined]
        assert isinstance(record.duration_ms, float)  # type: ignore[attr-defined]
    assert [r.path for r in records] == ["/api/health/live", "/api/nope"]  # type: ignore[attr-defined]


def test_valid_incoming_request_id_is_used(
    migrated_database: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-17."""
    caplog.set_level(logging.INFO)
    with running_app(migrated_database) as client:
        response = client.get("/api/health/live", headers={"X-Request-ID": "proxy-42"})
    assert response.headers["x-request-id"] == "proxy-42"
    assert _request_records(caplog)[0].correlation_id == "proxy-42"  # type: ignore[attr-defined]


# Non-ASCII arrives as raw bytes, as a proxy would send it (httpx refuses non-ASCII str headers).
@pytest.mark.parametrize("incoming", ["x" * 65, "bad id", "a_b", "şirket".encode()])
def test_invalid_incoming_request_id_is_replaced(
    migrated_database: Path, caplog: pytest.LogCaptureFixture, incoming: str | bytes
) -> None:
    """AC-17."""
    caplog.set_level(logging.INFO)
    with running_app(migrated_database) as client:
        response = client.get("/api/health/live", headers={"X-Request-ID": incoming})
    generated = response.headers["x-request-id"]
    assert re.fullmatch(r"[0-9a-f]{32}", generated)
    assert _request_records(caplog)[0].correlation_id == generated  # type: ignore[attr-defined]


def test_query_and_body_not_logged(
    migrated_database: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-18: neither query values nor the body appear in any log line."""
    caplog.set_level(logging.INFO)
    with running_app(migrated_database) as client:
        client.post(
            "/api/health/live?email=ali.veli%40example.com&tc=12345678901",
            json={"password": "Parola-123", "tc": "10987654321"},
        )
    formatter = JsonFormatter()
    logged = "\n".join(formatter.format(r) for r in _server_records(caplog))
    assert _request_records(caplog)
    for value in ("ali.veli", "example.com", "12345678901", "Parola-123", "10987654321", "email="):
        assert value not in logged
