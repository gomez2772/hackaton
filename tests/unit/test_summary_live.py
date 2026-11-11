"""Real client summary (B-2) on the demo fixture. Spends Claude tokens: run with `pytest -m live`."""

from __future__ import annotations

import pytest

from app import fakes
from app.engine.citations import validate
from app.engine.summary import summarize

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def summary():
    tr = fakes.transcript()
    return validate(summarize(tr, fakes.extraction()), tr)


def test_shape(summary):
    assert summary.title == "Resumen de tu reunión"
    assert 1 <= len(summary.points) <= 5 and 1 <= len(summary.next_steps) <= 3


def test_every_point_has_a_verified_quote(summary):
    for p in [*summary.points, *summary.next_steps]:
        assert p.evidence and all(e.verified for e in p.evidence), p.text


def test_key_facts_and_no_return_promise(summary):
    text = " ".join(p.text.lower() for p in [*summary.points, *summary.next_steps])
    assert "30 000 €" in text and "20 000 €" in text and "viernes" in text
    assert "perder dinero" not in text
