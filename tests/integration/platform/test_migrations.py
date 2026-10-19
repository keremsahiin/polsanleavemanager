import sqlite3
import threading
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.pool import QueuePool

from app.platform.db import create_app_engine
from app.platform.schema import current_revisions, latest_revisions
from tests.conftest import migrate


def _schema_snapshot(path: Path) -> list[tuple[str, str, str]]:
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT type, name, COALESCE(sql, '') FROM sqlite_master ORDER BY type, name"
        ).fetchall()
        versions = connection.execute("SELECT version_num FROM alembic_version").fetchall()
    connection.close()
    return [*rows, *(("version", v, "") for (v,) in versions)]


def test_upgrade_creates_file_and_reaches_head(database_path: Path) -> None:
    """AC-3: the upgrade command creates a missing file and brings it to the latest revision."""
    assert not database_path.exists()
    migrate(database_path)
    assert database_path.exists()
    engine = create_app_engine(database_path)
    try:
        assert current_revisions(engine) == latest_revisions() != frozenset()
    finally:
        engine.dispose()


def test_second_upgrade_is_noop(migrated_database: Path) -> None:
    """AC-3: running the upgrade again raises nothing and changes nothing."""
    before = _schema_snapshot(migrated_database)
    migrate(migrated_database)
    assert _schema_snapshot(migrated_database) == before


def test_app_engine_enforces_foreign_keys_and_wal(migrated_database: Path) -> None:
    """docs/conventions.md, Data rules: PRAGMA foreign_keys=ON and journal_mode=WAL."""
    engine = create_app_engine(migrated_database)
    try:
        with engine.connect() as connection:
            assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
            assert connection.execute(text("PRAGMA journal_mode")).scalar_one() == "wal"
    finally:
        engine.dispose()


def test_app_engine_serves_more_threads_than_pool_size_at_once(migrated_database: Path) -> None:
    """Review #1: FastAPI's thread pool runs >5 requests at once; every one keeps its connection."""
    threads = 8  # above SQLAlchemy's default pool_size of 5
    engine = create_app_engine(migrated_database)
    barrier = threading.Barrier(threads)
    errors: list[BaseException] = []

    def hold_connection_and_query() -> None:
        try:
            with engine.connect() as connection:
                barrier.wait(timeout=10)  # all connections are open at the same time
                assert connection.execute(text("SELECT 1")).scalar_one() == 1
                barrier.wait(timeout=10)
        except BaseException as exc:  # collected and asserted below
            errors.append(exc)

    workers = [threading.Thread(target=hold_connection_and_query) for _ in range(threads)]
    try:
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=30)
    finally:
        engine.dispose()
    assert errors == []
    assert isinstance(engine.pool, QueuePool)
