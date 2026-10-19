"""Landing page in a real browser against the real server (spec 0001, User experience)."""

import re
from collections.abc import Callable

import pytest
from playwright.sync_api import Page, Route, expect

pytestmark = pytest.mark.e2e

STATUS = "#system-status"
READY_REQUEST = "**/api/health/ready"
CHECKING = "Kontrol ediliyor…"
RUNNING = "Sistem çalışıyor"
UNREACHABLE = "Sisteme şu an ulaşılamıyor"


def _never_answer(_route: Route) -> None:
    """Leave the readiness request pending, as a hung server would."""


def _answer_not_ready(route: Route) -> None:
    route.fulfill(
        status=503,
        content_type="application/problem+json",
        body='{"code": "platform.not_ready", "status": 503}',
    )


def _fail_network(route: Route) -> None:
    route.abort("connectionrefused")


def test_title_and_language(page: Page, base_url: str) -> None:
    """AC-20."""
    page.goto(base_url)
    expect(page).to_have_title("Polsan İzin Yönetimi")
    expect(page.locator("html")).to_have_attribute("lang", "tr")
    expect(page.get_by_role("heading", level=1)).to_have_text("Polsan İzin Yönetimi")


def test_shows_checking_while_waiting(page: Page, base_url: str) -> None:
    """AC-21."""
    page.route(READY_REQUEST, _never_answer)
    page.goto(base_url)
    expect(page.locator(STATUS)).to_have_text(CHECKING)


def test_shows_running_when_ready(page: Page, base_url: str) -> None:
    """AC-22: no interception — the real server is ready."""
    page.goto(base_url)
    expect(page.locator(STATUS)).to_have_text(RUNNING)


def test_shows_unreachable_when_not_ready(page: Page, base_url: str) -> None:
    """AC-23."""
    page.route(READY_REQUEST, _answer_not_ready)
    page.goto(base_url)
    expect(page.locator(STATUS)).to_have_text(UNREACHABLE)


def test_shows_unreachable_on_network_error(page: Page, base_url: str) -> None:
    """AC-23."""
    page.route(READY_REQUEST, _fail_network)
    page.goto(base_url)
    expect(page.locator(STATUS)).to_have_text(UNREACHABLE)


def test_shows_unreachable_after_5s_timeout(page: Page, base_url: str) -> None:
    """AC-24: still checking just before 5 s, unreachable once 5 s have passed."""
    page.clock.install()
    page.route(READY_REQUEST, _never_answer)
    page.goto(base_url)
    status = page.locator(STATUS)
    expect(status).to_have_text(CHECKING)
    page.clock.run_for(4_900)
    expect(status).to_have_text(CHECKING)
    page.clock.run_for(200)
    expect(status).to_have_text(UNREACHABLE)


_COLOURS_JS = """el => {
  const transparent = c => c === "transparent" || c === "rgba(0, 0, 0, 0)";
  let node = el, background = "rgb(255, 255, 255)";
  while (node) {
    const c = getComputedStyle(node).backgroundColor;
    if (!transparent(c)) { background = c; break; }
    node = node.parentElement;
  }
  return [getComputedStyle(el).color, background];
}"""


def _relative_luminance(css_colour: str) -> float:
    red, green, blue = (int(v) / 255 for v in re.findall(r"\d+", css_colour)[:3])

    def linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    return 0.2126 * linear(red) + 0.7152 * linear(green) + 0.0722 * linear(blue)


def _contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(foreground), _relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


STATES: dict[str, tuple[Callable[[Route], None] | None, str]] = {
    "checking": (_never_answer, CHECKING),
    "running": (None, RUNNING),
    "unreachable": (_answer_not_ready, UNREACHABLE),
}


@pytest.mark.parametrize("state", sorted(STATES))
def test_status_is_live_region_with_sufficient_contrast(
    page: Page, base_url: str, state: str
) -> None:
    """AC-25: announced to screen readers; WCAG 2.1 AA contrast (>= 4.5:1) in every state."""
    handler, text = STATES[state]
    if handler is not None:
        page.route(READY_REQUEST, handler)
    page.goto(base_url)
    status = page.locator(STATUS)
    expect(status).to_have_text(text)
    expect(status).to_have_attribute("role", "status")
    expect(status).to_have_attribute("aria-live", "polite")
    foreground, background = status.evaluate(_COLOURS_JS)
    assert _contrast_ratio(foreground, background) >= 4.5
