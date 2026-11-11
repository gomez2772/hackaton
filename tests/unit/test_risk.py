"""Risk maths (C-04): known covariance and portfolio after recommendations."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app import fakes
from app.engine.risk import approx_volatility, portfolio_volatility, resulting_portfolio


def test_two_independent_assets_known_volatility():
    rng = np.random.default_rng(0)
    n = 200_000
    a = rng.normal(0, 0.01, n)
    b = rng.normal(0, 0.02, n)
    rets = pd.DataFrame({"A": a, "B": b})
    vol = portfolio_volatility({"A": 0.5, "B": 0.5}, rets)
    expected = np.sqrt(0.25 * 0.01**2 + 0.25 * 0.02**2) * np.sqrt(252) * 100
    assert abs(vol - expected) / expected < 0.01


def test_single_asset_approx_equals_class_midpoint():
    kids = fakes.kids()
    assert approx_volatility({"DEMO00000003": 1.0}, kids) == 16.0


def test_switch_funded_from_lowest_sri(demo_client, demo_extraction):
    pf = resulting_portfolio(demo_client, demo_extraction.recommendations, fakes.kids())
    assert pf == {"DEMO00000001": 50_000, "DEMO00000002": 20_000, "DEMO00000003": 30_000}


def test_two_correlated_assets_known_volatility():
    rng = np.random.default_rng(1)
    n, rho = 200_000, 0.6
    z1, z2 = rng.normal(size=n), rng.normal(size=n)
    a = 0.01 * z1
    b = 0.02 * (rho * z1 + np.sqrt(1 - rho**2) * z2)
    vol = portfolio_volatility({"A": 0.5, "B": 0.5}, pd.DataFrame({"A": a, "B": b}))
    var = 0.25 * 0.01**2 + 0.25 * 0.02**2 + 2 * 0.25 * rho * 0.01 * 0.02
    expected = np.sqrt(var) * np.sqrt(252) * 100
    assert abs(vol - expected) / expected < 0.01
