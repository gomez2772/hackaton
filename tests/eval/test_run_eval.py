"""D-4: the evaluation harness scores correctly. No API calls. Owner: D."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_eval as ev  # noqa: E402

from app import fakes  # noqa: E402
from app.config import STAGES, get_settings  # noqa: E402
from app.data.loaders import load_kids, load_risk_limits  # noqa: E402
from app.engine.checker import check  # noqa: E402
from app.engine.citations import locate  # noqa: E402
from app.schemas import (  # noqa: E402
    AnalysisResult,
    ConductCheck,
    ConductItem,
    ConductStatus,
    Evidence,
    Extraction,
    Recommendation,
    StatedNeed,
)

MEETINGS = {m.id: m for m in ev.load_meetings()}
KIDS = load_kids()
REAL_ISIN = {"equity_global": "IE00B03HD191", "equity_em": "IE0031786696", "bond_short_eur": "LU0290356871"}


def perfect(m: ev.Meeting) -> AnalysisResult:
    """What a flawless pipeline would return for meeting `m`."""
    tr = ev.script_transcript(m)
    quotes = [locate(q, tr) for q in m.truth["key_quotes"]]
    t = m.truth
    recs = [Recommendation(id=r["id"], product_name=r["asset_class"], isin=REAL_ISIN[r["asset_class"]],
                           action=r["action"], amount_eur=r["amount_eur"], rationale="", evidence=quotes[:1])
            for r in t["recommendations"]]
    needs = [StatedNeed(id=f"n{i}", kind=n["kind"], description="", amount_eur=n.get("amount_eur"),
                        horizon_years=n.get("horizon_years"), evidence=quotes[:1])
             for i, n in enumerate(t["stated_needs"], 1)]
    x = Extraction(recommendations=recs, stated_needs=needs,
                   commitments=[], circumstance_changes=[])
    flags = check(x, m.client, kids=KIDS, limits=load_risk_limits())
    conduct = ConductCheck(items=[ConductItem(code=c, title=c, rule="", status=ConductStatus(s), explanation="",
                                              evidence=quotes) for c, s in t["conduct"].items()])
    base = fakes.analysis_result()
    return base.model_copy(update={"client": m.client, "transcript": tr, "extraction": x, "flags": flags,
                                   "conduct": conduct, "client_summary": None})


def test_script_transcript_contains_every_key_quote():
    for m in MEETINGS.values():
        tr = ev.script_transcript(m)
        assert len(tr.segments) == len(m.turns)
        assert tr.segments[0].speaker_id == "speaker_0" and m.turns[0][0] == "advisor"
        assert all(a.end <= b.start for a, b in zip(tr.segments, tr.segments[1:], strict=False))
        for q in m.truth["key_quotes"]:
            assert locate(q, tr).verified, f"{m.id}: {q!r}"


@pytest.mark.parametrize("mid", sorted(MEETINGS))
def test_perfect_prediction_scores_100(mid):
    m = MEETINGS[mid]
    s = ev.score(m, perfect(m), KIDS)
    assert s["recommendations"]["recall"] == 1 and s["recommendations"]["precision"] == 1
    assert s["recommendations"]["amount_ok"] == len(m.truth["recommendations"])
    assert s["needs"]["fn"] == 0 and s["needs"]["fp"] == 0
    assert s["flags"]["correct"] == s["flags"]["total"]
    assert s["conduct"]["correct"] == s["conduct"]["total"] == 7
    assert s["quotes"]["key_found"] == s["quotes"]["key_total"]


def test_missed_breaches_and_wrong_flags_are_counted():
    m = MEETINGS["m03_promesa_presion"]
    r = perfect(m)
    lazy = ConductCheck(items=[it.model_copy(update={"status": ConductStatus.OK}) for it in r.conduct.items])
    red = [f.model_copy(update={"severity": type(f.severity)("red")}) for f in r.flags]
    s = ev.score(m, r.model_copy(update={"conduct": lazy, "flags": red}), KIDS)
    assert s["conduct"]["breach"]["recall"] == 0 and s["conduct"]["breach"]["fn"] == 2
    assert s["flags"]["correct"] == 0 and s["flags"]["red"]["fp"] == s["flags"]["total"]


def test_acceptable_alternative_is_not_a_false_positive():
    m = MEETINGS["m03_promesa_presion"]
    r = perfect(m)
    items = [it.model_copy(update={"status": ConductStatus.BREACH}) if it.code == "risks_explained" else it
             for it in r.conduct.items]
    s = ev.score(m, r.model_copy(update={"conduct": ConductCheck(items=items)}), KIDS)
    assert s["conduct"]["correct"] == 7 and s["conduct"]["breach"]["fp"] == 0


def test_recommendation_matched_by_keywords_without_isin():
    rec = Recommendation(id="r1", product_name="fondo indexado de renta variable de mercados emergentes",
                         action="buy", amount_eur=90000, rationale="", evidence=[])
    assert ev.asset_class(rec, {}) == "equity_em"
    extra = rec.model_copy(update={"action": "sell"})
    s = ev.score_recommendations([{"action": "buy", "asset_class": "equity_em", "amount_eur": 90000}], [rec, extra], {})
    assert (s["tp"], s["fp"], s["fn"], s["amount_ok"]) == (1, 1, 0, 1)


def test_unverified_quotes_do_not_count():
    s = ev.score_quotes(["me jubilo en tres años"], [Evidence(quote="me jubilo en tres años", verified=False)])
    assert s["key_found"] == 0 and s["verified"] == 0


def test_run_meeting_script_mode_uses_the_script_transcript(monkeypatch):
    """Full pipeline wiring with LLM stages faked: STT must come from the script, not the demo fixture."""
    no_llm = frozenset(STAGES) - {"stt"}
    monkeypatch.setattr(ev, "get_settings", lambda **_k: get_settings(fake_stages=no_llm))
    m = MEETINGS["m04_sin_aviso_riesgos"]
    r = ev.run_meeting(m, "script")
    assert r.transcript.segments[0].text == m.turns[0][1]
    assert [t.stage for t in r.timings][:1] == ["stt"]


def test_markdown_report_renders():
    m = MEETINGS["m05_correcta"]
    scores = [ev.score(m, perfect(m), KIDS)]
    doc = ev.markdown(scores, ev.aggregate(scores), "script", "modelo-x")
    assert "# EVAL.md" in doc and "| m05_correcta |" in doc and "Ninguno." in doc and "sintéticas" in doc
