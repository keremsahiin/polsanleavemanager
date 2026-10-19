from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.conftest import add_test_route, running_app


def _boom() -> object:
    raise RuntimeError("boom")


REQUESTS: dict[str, Callable[[TestClient], httpx.Response]] = {
    "api": lambda c: c.get("/api/health/live"),
    "not_ready_503": lambda c: c.get("/api/health/ready"),
    "not_found_404": lambda c: c.get("/api/nope"),
    "method_405": lambda c: c.post("/api/health/live"),
    "unexpected_500": lambda c: c.get("/api/_test/boom"),
}


@pytest.mark.parametrize("kind", sorted(REQUESTS))
def test_every_response_carries_security_headers(database_path: Path, kind: str) -> None:
    """AC-19 (API and error responses; the page is covered in test_static_page.py)."""
    # An unmigrated path, so the readiness call yields a real 503.
    with running_app(database_path, lambda app: add_test_route(app, "/api/_test/boom", _boom)) as c:
        response = REQUESTS[kind](c)
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "same-origin"
