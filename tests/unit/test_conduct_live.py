"""Real conduct check (B-2) on the demo fixture. Spends Claude tokens: run with `pytest -m live`."""

from __future__ import annotations

import pytest

from app import fakes
from app.engine.citations import validate
from app.engine.conduct import CHECKLIST, check_conduct

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def conduct():
    tr = fakes.transcript()
    return validate(check_conduct(tr, fakes.extraction()), tr)


def test_one_item_per_checklist_code(conduct):
    assert [it.code for it in conduct.items] == [c for c, *_ in CHECKLIST]
    assert conduct.model


def test_same_statuses_as_golden_fixture(conduct):
    golden = {it.code: it.status for it in fakes.conduct().items}
    assert {it.code: it.status for it in conduct.items} == golden


def test_every_quote_is_verified(conduct):
    unverified = [e.quote for it in conduct.items for e in it.evidence if not e.verified]
    assert not unverified, f"citas no literales: {unverified}"


def test_breaches_quote_the_advisor(conduct):
    tr = fakes.transcript()
    advisor = tr.segments[0].speaker_id
    seg_speaker = {s.id: s.speaker_id for s in tr.segments}
    for it in conduct.items:
        if it.status.value == "breach":
            assert any(seg_speaker.get(e.segment_id or "") == advisor for e in it.evidence), it.code
