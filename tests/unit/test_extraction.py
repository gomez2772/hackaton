"""ISIN resolution against the KID catalogue (B-4), without calling the API."""

from __future__ import annotations

from app import fakes
from app.engine.extraction import resolve_isins
from app.schemas import Extraction, Recommendation


def _rec(rid: str, isin: str | None, name: str = "fondo emergentes") -> Recommendation:
    return Recommendation(id=rid, product_name=name, isin=isin, action="buy", amount_eur=1000.0,
                          rationale="r", evidence=[])


def test_resolve_isins_keeps_valid_drops_invented_and_uses_kid_name():
    kids = fakes.kids()
    valid = next(iter(kids))
    ext = Extraction(recommendations=[_rec("r1", valid.lower()), _rec("r2", "XX0000000000"), _rec("r3", None)])
    out = resolve_isins(ext, kids)
    r1, r2, r3 = out.recommendations
    assert r1.isin == valid and r1.product_name == kids[valid].name
    assert r2.isin is None and r2.product_name == "fondo emergentes"
    assert r3.isin is None
    assert ext.recommendations[1].isin == "XX0000000000"  # input untouched
