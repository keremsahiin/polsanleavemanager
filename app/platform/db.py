"""SQLite engines (ADR 0002): foreign keys on, WAL journal; only migrations may create the file."""

import sqlite3
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.pool import ConnectionPoolEntry


def create_app_engine(database_path: Path) -> Engine:
    """Engine for the running app; opening fails if the file is missing (mode=rw never creates)."""
    uri = database_path.resolve().as_uri() + "?mode=rw"

    def connect() -> sqlite3.Connection:
        # FastAPI runs sync endpoints in a thread pool; the pool hands connections across threads.
        return sqlite3.connect(uri, uri=True, check_same_thread=False)

    return _with_pragmas(create_engine("sqlite://", creator=connect))


def create_migration_engine(database_path: Path) -> Engine:
    """Engine for Alembic: creates the file when it does not exist yet (spec 0001, AC-3)."""
    return _with_pragmas(create_engine(f"sqlite:///{database_path.resolve().as_posix()}"))


def _with_pragmas(engine: Engine) -> Engine:
    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection: sqlite3.Connection, _record: ConnectionPoolEntry) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine
