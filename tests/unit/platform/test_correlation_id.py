import re

import pytest

from app.platform.http import correlation_id_from


@pytest.mark.parametrize("incoming", ["abc-123", "A" * 64, "0", "proxy-req-7f3a"])
def test_well_formed_incoming_id_is_kept(incoming: str) -> None:
    """AC-17: up to 64 letters, digits and hyphens."""
    assert correlation_id_from(incoming) == incoming


@pytest.mark.parametrize(
    "incoming",
    [None, "", "A" * 65, "has space", "under_score", "semi;colon", "şirket", "x\nlog-injection"],
)
def test_missing_or_malformed_incoming_id_is_replaced(incoming: str | None) -> None:
    """AC-17: anything else is never echoed; a fresh id is generated instead."""
    generated = correlation_id_from(incoming)
    assert generated != incoming
    assert re.fullmatch(r"[0-9a-f]{32}", generated)


def test_generated_ids_are_unique() -> None:
    assert len({correlation_id_from(None) for _ in range(100)}) == 100
