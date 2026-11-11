"""D-3: the 5 evaluation meetings are internally consistent. No API calls. Owner: D."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import fakes
from app.engine.checker import check
from app.engine.citations import normalize
from app.engine.conduct import CHECKLIST
from app.schemas import ClientProfile, Evidence, Extraction, Recommendation, StatedNeed

MEETINGS = Path(__file__).resolve().parent / "meetings"
DIRS = sorted(p for p in MEETINGS.iterdir() if p.is_dir())
DEMO_ISIN = {k.asset_class: k.isin for k in fakes.kids().values()}
STATUSES = {"ok", "breach", "no_evidence"}


def load(d: Path, name: str) -> dict:
    return json.loads((d / f"{name}.json").read_text(encoding="utf-8"))


def test_five_meetings_with_the_agreed_mix():
    assert len(DIRS) == 5
    mix = sorted(load(d, "truth")["scenario"] for d in DIRS)
    assert mix == ["conduct_failure"] * 2 + ["correct"] + ["suitability_conflict"] * 2


@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_script_shape_and_length(d):
    s = load(d, "script")
    assert s["meeting_id"] == d.name and s["synthetic"] is True
    assert all(who in ("advisor", "client") and text.strip() for who, text in s["turns"])
    words = sum(len(text.split()) for _, text in s["turns"])
    assert 150 <= words <= 650, f"{words} palabras (objetivo ~1,5–2 min de audio, ver DECISIONS)"


@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_client_is_valid_and_matches(d):
    c = ClientProfile.model_validate(load(d, "client"))
    assert c.synthetic and c.client_id == load(d, "script")["client_id"]
    assert all(h.isin in fakes.kids() for h in c.portfolio)


@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_key_quotes_are_literal(d):
    turns = [normalize(t) for _, t in load(d, "script")["turns"]]
    for q in load(d, "truth")["key_quotes"]:
        assert any(normalize(q) in t for t in turns), f"cita no literal: {q!r}"


@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_conduct_truth_covers_the_checklist(d):
    t = load(d, "truth")
    assert set(t["conduct"]) == {c for c, *_ in CHECKLIST}
    assert set(t["conduct"].values()) <= STATUSES
    for code, allowed in t.get("conduct_acceptable", {}).items():
        assert t["conduct"][code] in allowed and set(allowed) <= STATUSES


@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_expected_flags_match_the_real_checker(d):
    """Feed the truth (as a perfect extraction) to the real checker with the demo funds."""
    t, client = load(d, "truth"), ClientProfile.model_validate(load(d, "client"))
    ev = [Evidence(quote="(truth)", verified=True)]
    recs = [Recommendation(id=r["id"], product_name=r["asset_class"], isin=DEMO_ISIN[r["asset_class"]],
                           action=r["action"], amount_eur=r["amount_eur"],
                           rationale=f"financiado con {r['funded_from']}", evidence=ev)
            for r in t["recommendations"]]
    needs = [StatedNeed(id=f"n{i}", kind=n["kind"], description="truth", amount_eur=n.get("amount_eur"),
                        horizon_years=n.get("horizon_years"), evidence=ev)
             for i, n in enumerate(t["stated_needs"], start=1)]
    flags = check(Extraction(recommendations=recs, stated_needs=needs), client,
                  kids=fakes.kids(), limits=fakes.risk_limits())
    got = {f.type.value: f.severity.value for f in flags}
    for ftype, expected in t["flags"].items():
        if expected is not None:
            assert got.get(ftype) == expected, f"{ftype}: esperado {expected}, comprobador {got.get(ftype)}"
