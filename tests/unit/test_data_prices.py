"""Versioned proxy prices (C-5): every KID proxy has ~3 years of daily closes and sane volatility."""

from __future__ import annotations

import numpy as np
import pytest

from app.data.loaders import DATA, load_kids, load_returns

pytestmark = pytest.mark.skipif(not any((DATA / "prices").glob("*.csv")), reason="sin precios descargados")


def test_every_proxy_has_three_years():
    kids = load_kids()
    rets = load_returns(sorted({k.proxy_ticker for k in kids.values()}))
    assert len(rets) >= 700 and not rets.isna().any().any()


def test_volatility_ordered_by_sri():
    kids = load_kids().values()
    rets = load_returns(sorted({k.proxy_ticker for k in kids}))
    vol = {k.isin: rets[k.proxy_ticker].std() * np.sqrt(252) * 100 for k in kids}
    low = max(vol[k.isin] for k in kids if k.sri <= 2)
    high = min(vol[k.isin] for k in kids if k.sri >= 4)
    assert low < high
