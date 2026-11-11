"""Real extraction (B-1) on the demo fixture transcript. Spends Claude tokens: run with `pytest -m live`."""

from __future__ import annotations

import pytest

from app import fakes
from app.data.loaders import load_kids
from app.engine.citations import validate
from app.engine.extraction import extract
from app.schemas import Role

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def extraction():
    tr = fakes.transcript()
    return validate(extract(tr, fakes.client()), tr)


def test_every_quote_is_verified(extraction):
    evidence = [e for grp in (extraction.circumstance_changes, extraction.stated_needs,
                              extraction.recommendations, extraction.commitments)
                for it in grp for e in it.evidence]
    assert evidence, "la extracción no trae citas"
    unverified = [e.quote for e in evidence if not e.verified]
    assert not unverified, f"citas no literales: {unverified}"
    for grp in (extraction.circumstance_changes, extraction.stated_needs,
                extraction.recommendations, extraction.commitments):
        assert all(it.evidence for it in grp)


def test_single_buy_recommendation_r1(extraction):
    assert len(extraction.recommendations) == 1, "la venta de renta fija es financiación, no otra recomendación"
    r1 = extraction.recommendations[0]
    assert r1.id == "r1" and r1.action == "buy" and r1.amount_eur == 30000
    kid = load_kids().get(r1.isin or "")
    assert kid is not None and "emergente" in kid.name.lower(), f"ISIN no emparejado: {r1.isin}"
    assert "renta fija" in r1.rationale.lower()


def test_needs_n1_n2_n3(extraction):
    by_kind = {n.kind: n for n in extraction.stated_needs}
    assert by_kind["horizon"].horizon_years == 3
    assert by_kind["liquidity"].amount_eur == 20000 and by_kind["liquidity"].horizon_years == 1
    assert "capital_preservation" in by_kind
    assert not [c for c in extraction.circumstance_changes if c.field == "liquidity_need"], "duplica n2"


def test_change_cc1_and_commitment_c1(extraction):
    assert any(c.field == "horizon" for c in extraction.circumstance_changes)
    c1 = extraction.commitments[0]
    assert c1.who == Role.ADVISOR and "viernes" in (c1.due or "").lower()


def test_speaker_roles(extraction):
    assert extraction.speaker_roles == {"speaker_0": Role.ADVISOR, "speaker_1": Role.CLIENT}
