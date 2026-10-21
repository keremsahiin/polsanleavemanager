"""e2e fixtures. This file is the single owner of the app-under-test and browser lifecycles:
both are started for the run and stopped in `finally`, also on failure and timeout
(docs/testing.md, Resource hygiene; ADR 0003: Playwright without the pytest plugin).
"""

import os
import socket
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

from tests.conftest import migrate

REPO_ROOT = Path(__file__).resolve().parents[2]
STARTUP_TIMEOUT_S = 30
STOP_TIMEOUT_S = 5


# tryfirst: the marker must exist before -m "not e2e" deselects items.
@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Everything under tests/e2e is e2e, marked or not: it can never slip into the fast profile."""
    e2e_dir = Path(__file__).parent
    for item in items:
        if e2e_dir in Path(item.path).parents:
            item.add_marker(pytest.mark.e2e)


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
        return port


def _wait_until_live(base_url: str, server: subprocess.Popen[bytes], log_file: Path) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_S
    while time.monotonic() < deadline:
        if server.poll() is not None:
            pytest.fail(f"app exited with {server.returncode}:\n{log_file.read_text('utf-8')}")
        try:
            with urllib.request.urlopen(f"{base_url}/api/health/live", timeout=1):  # noqa: S310
                return
        except OSError:
            time.sleep(0.2)
    pytest.fail(f"app not live after {STARTUP_TIMEOUT_S} s:\n{log_file.read_text('utf-8')}")


def _stop(server: subprocess.Popen[bytes]) -> None:
    server.terminate()
    try:
        server.wait(timeout=STOP_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(timeout=STOP_TIMEOUT_S)


@dataclass(frozen=True)
class LiveServer:
    url: str
    log_file: Path  # everything the process writes to stdout/stderr, unbuffered


@pytest.fixture(scope="session")
def live_server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[LiveServer]:
    """The real entry point (python -m app) on a free loopback port, with a migrated database."""
    work_dir = tmp_path_factory.mktemp("e2e")
    database_path = work_dir / "plm.db"
    migrate(database_path)
    port = _free_port()
    env = {
        **os.environ,
        "PLM_DATABASE_PATH": str(database_path),
        "PLM_HOST": "127.0.0.1",
        "PLM_PORT": str(port),
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1",  # log lines reach server.log as they are written
    }
    log_file = work_dir / "server.log"
    with log_file.open("wb") as log:
        server = subprocess.Popen(
            [sys.executable, "-m", "app"], cwd=REPO_ROOT, env=env, stdout=log, stderr=log
        )
        try:
            url = f"http://127.0.0.1:{port}"
            _wait_until_live(url, server, log_file)
            yield LiveServer(url=url, log_file=log_file)
        finally:
            _stop(server)


@pytest.fixture(scope="session")
def base_url(live_server: LiveServer) -> str:
    return live_server.url


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        chromium = playwright.chromium.launch(headless=True)
        try:
            yield chromium
        finally:
            chromium.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context(locale="tr-TR")
    try:
        yield context.new_page()
    finally:
        context.close()
