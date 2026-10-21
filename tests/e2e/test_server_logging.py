"""Logs of the real process (python -m app under uvicorn), not of the in-process TestClient.

Guards what only the entry point configures: uvicorn's access log is off (it would write query
strings), log_config=None keeps every line JSON, alembic stays below INFO (review 0001 #2, #3).
"""

import json
import time
import urllib.error
import urllib.request

import pytest

from tests.e2e.conftest import LiveServer

pytestmark = pytest.mark.e2e

PERSONAL_VALUES = ("ali.veli", "example.com", "12345678901", "10987654321", "Parola-123")


def _send(url: str, request_id: str, method: str = "GET", body: bytes | None = None) -> None:
    request = urllib.request.Request(  # noqa: S310 — fixed http://127.0.0.1 URL from the fixture
        url,
        data=body,
        method=method,
        headers={"X-Request-ID": request_id, "Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(request, timeout=5).close()  # noqa: S310
    except urllib.error.HTTPError as error:  # 405 / 503 are answers too
        error.close()


def _parse(line: str) -> dict[str, object]:
    try:
        entry: dict[str, object] = json.loads(line)
    except json.JSONDecodeError:
        pytest.fail(f"server wrote a non-JSON log line: {line!r}")
    return entry


def _entries_once_logged(server: LiveServer, request_ids: set[str]) -> list[dict[str, object]]:
    deadline = time.monotonic() + 10
    while True:
        # The server keeps writing while we read: only lines it has finished (ending in a newline)
        # are parsed; every one of those must be JSON (review 0001 F2).
        lines = server.log_file.read_text("utf-8").splitlines(keepends=True)
        entries = [_parse(line) for line in lines if line.endswith("\n") and line.strip()]
        if request_ids <= {e.get("correlation_id") for e in entries} or time.monotonic() > deadline:
            return entries
        time.sleep(0.1)


def test_real_server_logs_one_json_line_per_request_without_personal_data(
    live_server: LiveServer,
) -> None:
    """AC-16, AC-18 (and R-8) on the real entry point."""
    url = live_server.url
    _send(f"{url}/api/health/live?email=ali.veli%40example.com&tc=12345678901", "log-e2e-query")
    body = b'{"tc": "10987654321", "password": "Parola-123"}'
    _send(f"{url}/api/health/live", "log-e2e-body", method="POST", body=body)
    _send(f"{url}/api/health/ready", "log-e2e-ready")
    request_ids = {"log-e2e-query", "log-e2e-body", "log-e2e-ready"}

    entries = _entries_once_logged(live_server, request_ids)

    for request_id in request_ids:
        lines = [e for e in entries if e.get("correlation_id") == request_id]
        assert len(lines) == 1, request_id
        assert lines[0]["logger"] == "app.request"
        assert set(lines[0]) >= {"time", "level", "method", "path", "status", "duration_ms"}
    loggers = {str(e["logger"]) for e in entries}
    assert not any(name.startswith(("uvicorn.access", "alembic")) for name in loggers)
    raw = live_server.log_file.read_text("utf-8")
    for value in PERSONAL_VALUES:
        assert value not in raw
