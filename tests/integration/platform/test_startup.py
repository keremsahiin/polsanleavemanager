import os
import subprocess
import sys
from pathlib import Path

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
