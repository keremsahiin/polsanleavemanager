"""Application settings, read from environment variables (docs/development.md)."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DATABASE_PATH_VAR = "PLM_DATABASE_PATH"
HOST_VAR = "PLM_HOST"
PORT_VAR = "PLM_PORT"

# Loopback by default: the app is reached only through the HTTPS reverse proxy (ADR 0002).
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


class SettingsError(Exception):
    """Configuration is missing or invalid; the message is shown to the operator in Turkish."""


@dataclass(frozen=True)
class Settings:
    database_path: Path
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT


def load_settings(environ: Mapping[str, str]) -> Settings:
    """Build settings from an environment mapping; deliberately no default database path."""
    raw_path = environ.get(DATABASE_PATH_VAR, "").strip()
    if not raw_path:
        raise SettingsError(
            f"{DATABASE_PATH_VAR} ortam değişkeni tanımlı değil. "
            "Veritabanı dosyasının yolunu bu değişkenle verin (bkz. .env.example)."
        )
    host = environ.get(HOST_VAR, "").strip() or DEFAULT_HOST
    return Settings(database_path=Path(raw_path), host=host, port=_parse_port(environ))


def _parse_port(environ: Mapping[str, str]) -> int:
    raw_port = environ.get(PORT_VAR, "").strip()
    if not raw_port:
        return DEFAULT_PORT
    if not raw_port.isdigit() or not 1 <= int(raw_port) <= 65535:
        raise SettingsError(f"{PORT_VAR} 1 ile 65535 arasında bir tamsayı olmalı.")
    return int(raw_port)
