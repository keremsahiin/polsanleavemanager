import logging
from pathlib import Path

import pytest
from fastapi import FastAPI

from app.platform.errors import DomainError
from tests.conftest import add_test_route, running_app

PROBLEM_KEYS = {"type", "title", "status", "detail", "code"}
INTERNAL_DETAIL = "gizli-detay C:\\veri\\plm.db"


class _Conflict(DomainError):
    code = "test.conflict"
    status = 409
    title = "Çakışma"


def _boom() -> object:
    raise RuntimeError(INTERNAL_DETAIL)


def _domain_failure() -> object:
    raise _Conflict("Kayıt çakışıyor.")


def _with_failing_routes(app: FastAPI) -> None:
    add_test_route(app, "/api/_test/boom", _boom)
    add_test_route(app, "/api/_test/conflict", _domain_failure)


def test_unknown_api_path_returns_problem_json(migrated_database: Path) -> None:
    """AC-12."""
    with running_app(migrated_database) as client:
        response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert set(body) == PROBLEM_KEYS
    assert body["status"] == 404
    assert body["code"] == "platform.not_found"
    assert body["title"] == "Bulunamadı"
    assert body["detail"] == "İstenen adres bulunamadı."


def test_unsupported_method_returns_405_problem_json(migrated_database: Path) -> None:
    """AC-13."""
    with running_app(migrated_database) as client:
        response = client.post("/api/health/live")
    assert response.status_code == 405
    assert response.headers["content-type"] == "application/problem+json"
    assert "GET" in response.headers["allow"]
    body = response.json()
    assert set(body) == PROBLEM_KEYS
    assert body["code"] == "platform.method_not_allowed"
    assert body["title"] == "Yöntem desteklenmiyor"
    assert body["detail"] == "Bu adres, istekte kullanılan yöntemi desteklemiyor."


def test_unexpected_error_returns_500_without_details(migrated_database: Path) -> None:
    """AC-14: Turkish message and correlation id; no stack trace, exception text or path."""
    with running_app(migrated_database, _with_failing_routes) as client:
        response = client.get("/api/_test/boom")
    assert response.status_code == 500
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert set(body) == PROBLEM_KEYS | {"correlation_id"}
    assert body["code"] == "platform.internal_error"
    assert body["title"] == "Beklenmeyen bir hata oluştu"
    assert body["detail"] == (
        "İsteğiniz işlenirken beklenmeyen bir hata oluştu. Sorun sürerse bu kimlikle "
        "destek ekibine başvurun."
    )
    assert body["correlation_id"] == response.headers["x-request-id"]
    for leak in ("gizli-detay", "plm.db", "RuntimeError", "Traceback", "test_errors.py"):
        assert leak not in response.text


def test_unexpected_error_detail_logged_with_same_correlation_id(
    migrated_database: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-15."""
    caplog.set_level(logging.INFO)
    with running_app(migrated_database, _with_failing_routes) as client:
        response = client.get("/api/_test/boom")
    correlation_id = response.json()["correlation_id"]
    errors = [r for r in caplog.records if r.name == "app.error"]
    assert len(errors) == 1
    assert errors[0].correlation_id == correlation_id  # type: ignore[attr-defined]
    assert errors[0].exc_info is not None
    assert INTERNAL_DETAIL in str(errors[0].exc_info[1])


def test_domain_error_becomes_its_problem(migrated_database: Path) -> None:
    """docs/conventions.md, Error handling: a coded DomainError keeps its status and code."""
    with running_app(migrated_database, _with_failing_routes) as client:
        response = client.get("/api/_test/conflict")
    assert response.status_code == 409
    assert response.json()["code"] == "test.conflict"
    assert response.json()["detail"] == "Kayıt çakışıyor."
