"""Portfolio risk maths. Owner: C. Task C-04."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.schemas import ClientProfile, Recommendation

TRADING_DAYS = 252


def portfolio_volatility(weights: dict[str, float], returns: pd.DataFrame) -> float:
    """Annualised volatility in % for weights (summing to 1) over daily returns columns."""
    cols = [c for c in weights if weights[c] != 0]
    w = np.array([weights[c] for c in cols])
    cov = returns[cols].cov().to_numpy() * TRADING_DAYS
    return float(np.sqrt(w @ cov @ w) * 100)


def resulting_portfolio(client: ClientProfile, recs: list[Recommendation]) -> dict[str, float]:
    """Amount per ISIN after applying recommendations.

    TODO(C-04): buy adds; sell/switch subtract (switch also needs the source, see rationale);
    when a buy has no explicit funding, scale the rest proportionally or add cash.
    """
    raise NotImplementedError("C-04: resulting_portfolio() pendiente.")
