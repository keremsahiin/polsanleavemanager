from pathlib import Path

import pytest

from app.platform.settings import (
    DATABASE_PATH_VAR,
    DEFAULT_HOST,
    DEFAULT_PORT,
    SettingsError,
    load_settings,
)


@pytest.mark.parametrize("environ", [{}, {DATABASE_PATH_VAR: ""}, {DATABASE_PATH_VAR: "   "}])
def test_missing_database_path_raises(environ: dict[str, str]) -> None:
    """AC-2: no database path, no settings; the message names the variable, in Turkish."""
    with pytest.raises(SettingsError) as excinfo:
        load_settings(environ)
    assert DATABASE_PATH_VAR in str(excinfo.value)
    assert "tanımlı değil" in str(excinfo.value)


def test_database_path_only_uses_loopback_defaults() -> None:
    settings = load_settings({DATABASE_PATH_VAR: "data/plm.db"})
    assert settings.database_path == Path("data/plm.db")
    assert settings.host == DEFAULT_HOST == "127.0.0.1"
    assert settings.port == DEFAULT_PORT == 8000


def test_host_and_port_can_be_overridden() -> None:
    settings = load_settings(
        {DATABASE_PATH_VAR: "plm.db", "PLM_HOST": "0.0.0.0", "PLM_PORT": "8123"}  # noqa: S104
    )
    assert (settings.host, settings.port) == ("0.0.0.0", 8123)  # noqa: S104


@pytest.mark.parametrize("port", ["abc", "0", "65536", "-1", "80.5"])
def test_invalid_port_raises(port: str) -> None:
    with pytest.raises(SettingsError, match="PLM_PORT"):
        load_settings({DATABASE_PATH_VAR: "plm.db", "PLM_PORT": port})
