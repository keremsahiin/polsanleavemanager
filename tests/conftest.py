"""Shared fixtures: every test gets its own temporary SQLite file (docs/testing.md)."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from alembic import command
from fastapi.testclient import TestClient

from app.main import create_app
from app.platform.schema import alembic_config
from app.platform.settings import Settings


def migrate(database_path: Path) -> None:
    """Bring a database file to the latest schema, exactly as `alembic upgrade head` does."""
    command.upgrade(alembic_config(database_path), "head")


def table_names(database_path: Path) -> set[str]:
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    connection.close()
    return {name for (name,) in rows}


@contextmanager
def running_app(database_path: Path) -> Iterator[TestClient]:
    """The app with its lifespan running (engine disposed on exit — Windows keeps files locked)."""
    with TestClient(create_app(Settings(database_path=database_path))) as client:
        yield client


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "plm.db"


@pytest.fixture
def migrated_database(database_path: Path) -> Path:
    migrate(database_path)
    return database_path


@pytest.fixture
def client(migrated_database: Path) -> Iterator[TestClient]:
    with running_app(migrated_database) as test_client:
        yield test_client
