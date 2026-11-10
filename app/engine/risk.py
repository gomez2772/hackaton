"""Portfolio risk maths. Owner: C. Task C-04.

Volatility: covariance of daily proxy returns when prices exist (C-5); otherwise an
approximation from the PRIIPs SRI class mid-points with correlation 0.8 between risky assets
(declared in DECISIONS.md), so the demo never depends on internet or price files.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.schemas import ClientProfile, FundKID, Recommendation

TRADING_DAYS = 252
# Mid-point of each PRIIPs volatility class (SRI 1..7), annual %
VOL_BY_SRI = {1: 0.3, 2: 3.0, 3: 8.5, 4: 16.0, 5: 25.0, 6: 40.0, 7: 90.0}
RISKY_CORRELATION = 0.8


def portfolio_volatility(weights: dict[str, float], returns: pd.DataFrame) -> float:
    """Annualised volatility in % for weights (summing to 1) over daily returns columns."""
    cols = [c for c in weights if weights[c] != 0]
    w = np.array([weights[c] for c in cols])
    cov = returns[cols].cov().to_numpy() * TRADING_DAYS
    return float(np.sqrt(w @ cov @ w) * 100)


def approx_volatility(weights: dict[str, float], kids: dict[str, FundKID]) -> float:
    """Annualised volatility in % from SRI classes (weights by ISIN)."""
    isins = [i for i, w in weights.items() if w and i in kids]
    if not isins:
        return 0.0
    w = np.array([weights[i] for i in isins])
    vol = np.array([VOL_BY_SRI[kids[i].sri] for i in isins]) / 100
    risky = np.array([kids[i].sri >= 3 for i in isins])
    corr = np.where(np.outer(risky, risky), RISKY_CORRELATION, 0.0)
    np.fill_diagonal(corr, 1.0)
    return float(np.sqrt(w @ (np.outer(vol, vol) * corr) @ w) * 100)


def resulting_portfolio(client: ClientProfile, recs: list[Recommendation],
                        kids: dict[str, FundKID] | None = None) -> dict[str, float]:
    """Amount per ISIN after applying recommendations.

    buy/switch add to the target; the money comes from the lowest-SRI holding (typically the
    money-market or short-term bond fund), spilling over to the next ones if it is not enough.
    sell subtracts from the target. hold changes nothing.
    """
    kids = kids or {}
    pf: dict[str, float] = {}
    for h in client.portfolio:
        pf[h.isin] = pf.get(h.isin, 0.0) + h.amount_eur
    for r in recs:
        if not r.isin or not r.amount_eur or r.action == "hold":
            continue
        if r.action == "sell":
            pf[r.isin] = max(0.0, pf.get(r.isin, 0.0) - r.amount_eur)
            continue
        pending = r.amount_eur
        sources = sorted((i for i in pf if i != r.isin and pf[i] > 0),
                         key=lambda i: kids[i].sri if i in kids else 9)
        for i in sources:
            take = min(pf[i], pending)
            pf[i] -= take
            pending -= take
            if pending <= 0:
                break
        pf[r.isin] = pf.get(r.isin, 0.0) + r.amount_eur  # any unfunded part is new money
    return {i: round(v, 2) for i, v in pf.items() if v > 0}
