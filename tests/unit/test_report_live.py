"""Real Claude rewrite of the report (B-6) on the demo fixture. Spends tokens: run with `pytest -m live`."""

from __future__ import annotations

import pytest

from app import fakes
from app.engine.report import draft

pytestmark = pytest.mark.live


def test_polished_report_keeps_coverage_and_verdict():
    args = (fakes.extraction(), fakes.flags(), fakes.client(), fakes.transcript())
    base = draft(*args, advisor_name="A", meeting_date="2026-11-10")
    out = draft(*args, advisor_name="A", meeting_date="2026-11-10", polish=True)
    assert out.model.startswith("plantilla+")
    assert out.coverage_pct == 100.0 == base.coverage_pct
    text = " ".join(s.text for sec in out.sections for s in sec.sentences).lower()
    assert "no es idónea" in text and "30 000 €" in text
    changed = sum(a.text != b.text for sa, sb in zip(out.sections, base.sections, strict=True)
                  for a, b in zip(sa.sentences, sb.sentences, strict=True))
    assert changed > 0
