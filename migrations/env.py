"""Alembic environment: the database file comes from PLM_DATABASE_PATH (docs/development.md)."""

import os
from pathlib import Path

from alembic import context

from app.platform.db import create_migration_engine
from app.platform.settings import load_settings


def _database_path() -> Path:
    explicit = context.config.attributes.get("database_path")
    if explicit is not None:
        return Path(explicit)
    return load_settings(os.environ).database_path


def run_migrations_online() -> None:
    engine = create_migration_engine(_database_path())
    try:
        with engine.connect() as connection:
            # Batch mode: SQLite cannot ALTER most constraints in place.
            context.configure(connection=connection, target_metadata=None, render_as_batch=True)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise SystemExit("Offline (SQL script) migrations are not supported.")
run_migrations_online()
