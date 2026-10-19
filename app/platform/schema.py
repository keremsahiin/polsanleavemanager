"""Schema version of the database versus the latest migration (readiness, spec 0001 R-5)."""

from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def alembic_config(database_path: Path | None = None) -> Config:
    """Alembic config; an explicit database path overrides PLM_DATABASE_PATH (migrations/env.py)."""
    config = Config(str(ALEMBIC_INI))
    if database_path is not None:
        config.attributes["database_path"] = database_path
    return config


def latest_revisions() -> frozenset[str]:
    return frozenset(ScriptDirectory.from_config(alembic_config()).get_heads())


def current_revisions(engine: Engine) -> frozenset[str]:
    """Read-only: an unmigrated database has no version table and yields an empty set."""
    with engine.connect() as connection:
        return frozenset(MigrationContext.configure(connection).get_current_heads())
