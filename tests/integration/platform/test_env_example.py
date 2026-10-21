from pathlib import Path

from app.platform.settings import DATABASE_PATH_VAR, HOST_VAR, PORT_VAR, load_settings

ENV_EXAMPLE = Path(__file__).resolve().parents[3] / ".env.example"
SECRET_HINTS = ("SECRET", "PASSWORD", "TOKEN", "KEY")


def _parse(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            name, _, value = stripped.partition("=")
            entries[name.strip()] = value.strip()
    return entries


def test_env_example_lists_every_setting_without_secrets() -> None:
    """AC-6: every variable the app reads is listed, the example works, and holds no secret."""
    entries = _parse(ENV_EXAMPLE.read_text(encoding="utf-8"))
    assert set(entries) == {DATABASE_PATH_VAR, HOST_VAR, PORT_VAR}
    load_settings(entries)  # the example itself is a valid configuration
    for name, value in entries.items():
        assert not (any(hint in name for hint in SECRET_HINTS) and value)
