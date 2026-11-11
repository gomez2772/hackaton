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


def test_requirement_ids_exist_in_local_checklist():
    from app.data.regulation import valid_ids
    from app.engine.conduct import REQUIREMENT_IDS

    codes = {c for c, *_ in CHECKLIST}
    assert set(REQUIREMENT_IDS) <= codes
    assert {i for ids in REQUIREMENT_IDS.values() for i in ids} <= valid_ids()


def test_rule_gets_ids_and_invented_ids_are_removed():
    raw = ConductCheck(items=[ConductItem(code="recording_notice", title="x", rule="y", status=ConductStatus.OK,
                                          explanation="Se avisa de la grabación (REG-01), según REG-99.")])
    rec = _complete(raw, "m").items[0]
    assert rec.rule.endswith("· REG-01")
    assert "REG-01" in rec.explanation and "REG-99" not in rec.explanation
