"""Real extraction (B-1, B-4) on the real demo clip transcript, the real demo client and the real
KID catalogue. Spends Claude tokens: run with `pytest -m live`."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.data.loaders import load_client, load_kids
from app.engine.citations import validate
from app.engine.extraction import extract
from app.schemas import Role, Transcript

pytestmark = pytest.mark.live
CLIP = Path(__file__).resolve().parents[2] / "app" / "data" / "audio" / "demo_clip.transcript.json"


@pytest.fixture(scope="module")
def client():
    return load_client("CLI-DEMO-001")


@pytest.fixture(scope="module")
def extraction(client):
    tr = Transcript.model_validate_json(CLIP.read_text(encoding="utf-8"))
    return validate(extract(tr, client), tr)


def test_every_quote_is_verified(extraction):
    groups = (extraction.circumstance_changes, extraction.stated_needs,
              extraction.recommendations, extraction.commitments)
    evidence = [e for grp in groups for it in grp for e in it.evidence]
    assert evidence, "la extracción no trae citas"
    unverified = [e.quote for e in evidence if not e.verified]
    assert not unverified, f"citas no literales: {unverified}"
    assert all(it.evidence for grp in groups for it in grp)


def test_single_buy_with_real_isin_and_funding_source(extraction, client):
    assert len(extraction.recommendations) == 1, "la venta de renta fija es financiación, no otra recomendación"
    r1 = extraction.recommendations[0]
    assert r1.id == "r1" and r1.action == "buy" and r1.amount_eur == 30000
    kids = load_kids()
    assert r1.isin in kids and kids[r1.isin].asset_class == "equity_em", f"ISIN no emparejado: {r1.isin}"
    assert r1.product_name == kids[r1.isin].name
    bonds = [h.isin for h in client.portfolio if h.isin in kids and kids[h.isin].asset_class.startswith("bond")]
    assert any(isin in r1.rationale for isin in bonds), f"origen del dinero sin ISIN: {r1.rationale}"


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
