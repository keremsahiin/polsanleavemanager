import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.conftest import running_app

PROBLEM_KEYS = {"type", "title", "status", "detail", "code"}


def _missing_file(path: Path) -> Path:
    return path


def _directory_instead_of_file(path: Path) -> Path:
    path.mkdir()
    return path


def _unmigrated_file(path: Path) -> Path:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
    connection.close()
    return path


def _unknown_revision(path: Path) -> Path:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        connection.execute("INSERT INTO alembic_version VALUES ('0000')")
    connection.close()
    return path


NOT_READY_SETUPS: dict[str, Callable[[Path], Path]] = {
    "missing_file": _missing_file,
    "directory_instead_of_file": _directory_instead_of_file,
    "unmigrated_file": _unmigrated_file,
    "unknown_revision": _unknown_revision,
}


def test_live_succeeds_with_current_schema(client: TestClient) -> None:
    """AC-1."""
    response = client.get("/api/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_with_current_schema(client: TestClient) -> None:
    """AC-7."""
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.parametrize("setup", ["unmigrated_file", "unknown_revision"])
def test_ready_503_when_schema_not_current(database_path: Path, setup: str) -> None:
    """AC-8."""
    path = NOT_READY_SETUPS[setup](database_path)
    with running_app(path) as client:
        response = client.get("/api/health/ready")
    assert response.status_code == 503
    assert response.json()["code"] == "platform.not_ready"


def test_ready_503_when_file_missing(database_path: Path) -> None:
    """AC-9."""
    with running_app(database_path) as client:
        response = client.get("/api/health/ready")
    assert response.status_code == 503


def test_ready_503_when_path_is_unreadable(database_path: Path) -> None:
    """AC-9: the path exists but cannot be opened as a database."""
    with running_app(_directory_instead_of_file(database_path)) as client:
        response = client.get("/api/health/ready")
    assert response.status_code == 503


@pytest.mark.parametrize("setup", sorted(NOT_READY_SETUPS))
def test_not_ready_body_leaks_no_details(database_path: Path, setup: str) -> None:
    """AC-10: no path, no error text, no schema version in the not-ready response."""
    path = NOT_READY_SETUPS[setup](database_path)
    with running_app(path) as client:
        response = client.get("/api/health/ready")
    assert response.status_code == 503
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert set(body) == PROBLEM_KEYS
    text = response.text.lower()
    for leak in (str(path).lower(), path.name.lower(), "sqlite", "alembic", "0001", "0000"):
        assert leak not in text


def test_health_needs_no_session(client: TestClient) -> None:
    """AC-11: no cookie, no credentials — both signals still answer."""
    client.cookies.clear()
    assert client.get("/api/health/live").status_code == 200
    assert client.get("/api/health/ready").status_code == 200
