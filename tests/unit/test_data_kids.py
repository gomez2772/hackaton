"""Real KID catalogue (C-3): app/data/kids.json validates against FundKID and meets the minimum mix."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date

import pytest

from app.data.loaders import DATA, load_kids
from app.schemas import FundKID

KIDS = DATA / "kids.json"
pytestmark = pytest.mark.skipif(not KIDS.exists(), reason="app/data/kids.json no existe todavía")


def test_catalogue_validates_and_has_unique_isins():
    raw = json.loads(KIDS.read_text(encoding="utf-8"))
    funds = [FundKID.model_validate(k) for k in raw]
    assert len(funds) == len({f.isin for f in funds}) >= 8
    assert load_kids().keys() == {f.isin for f in funds}


def test_minimum_asset_mix():
    classes = Counter(k.asset_class for k in load_kids().values())
    assert classes["equity_em"] >= 1 and classes["equity_global"] >= 1
    assert classes["bond_short_eur"] >= 2 and classes["money_market"] >= 1


def test_every_fund_has_a_real_source():
    for k in load_kids().values():
        assert len(k.isin) == 12 and k.isin[:2].isalpha(), k.isin
        assert k.source_url.startswith("https://"), k.isin
        assert date.fromisoformat(k.kid_date) <= date.today(), k.isin
        assert 0 < k.ongoing_costs_pct < 2 and k.recommended_holding_years > 0, k.isin
        assert k.proxy_ticker, k.isin
