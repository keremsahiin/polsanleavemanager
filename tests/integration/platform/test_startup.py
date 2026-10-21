import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from tests.conftest import running_app, table_names

REPO_ROOT = Path(__file__).resolve().parents[3]


def _env_without_plm_settings() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("PLM_")}
    env["PYTHONUTF8"] = "1"  # decode the message deterministically, whatever the console code page
    return env


def test_start_without_database_path_exits_nonzero_with_turkish_message() -> None:
    """AC-2: the real entry point refuses to start without PLM_DATABASE_PATH."""
    result = subprocess.run(
        [sys.executable, "-m", "app"],
        cwd=REPO_ROOT,
        env=_env_without_plm_settings(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    assert result.returncode != 0
    assert "PLM_DATABASE_PATH" in result.stderr
    assert "başlatılamadı" in result.stderr


def test_app_start_does_not_migrate_schema(database_path: Path) -> None:
    """AC-4: starting against a never-migrated database leaves its schema version empty."""
    sqlite3.connect(database_path).close()  # an empty, never-migrated database file
    with running_app(database_path) as client:
        client.get("/api/health/live")
        client.get("/api/health/ready")
    assert "alembic_version" not in table_names(database_path)


def test_missing_database_file_is_not_created(database_path: Path) -> None:
    """AC-5: neither starting nor asking for readiness creates the database file."""
    with running_app(database_path) as client:
        client.get("/api/health/live")
        client.get("/api/health/ready")
    assert list(database_path.parent.iterdir()) == []
