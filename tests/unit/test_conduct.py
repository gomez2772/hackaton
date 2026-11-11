"""Conduct post-processing (B-2) without calling the API."""

from __future__ import annotations

from app.engine.conduct import CHECKLIST, _complete
from app.schemas import ConductCheck, ConductItem, ConductStatus


def test_complete_keeps_order_drops_unknown_and_fills_missing():
    raw = ConductCheck(items=[
        ConductItem(code="return_promise", title="x", rule="y", status=ConductStatus.BREACH, explanation="e"),
        ConductItem(code="invented", title="x", rule="y", status=ConductStatus.OK, explanation="e"),
    ])
    out = _complete(raw, "m")
    assert [it.code for it in out.items] == [c for c, *_ in CHECKLIST]
    by = {it.code: it for it in out.items}
    assert by["return_promise"].status == ConductStatus.BREACH
    assert by["return_promise"].rule == dict((c, r) for c, _, r, _ in CHECKLIST)["return_promise"]
    assert by["costs_disclosed"].status == ConductStatus.NO_EVIDENCE
    assert out.model == "m"
