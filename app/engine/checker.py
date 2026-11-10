"""Quantitative suitability checker (deterministic, no LLM). Owner: C. Task C-04.

Severity rules: docs/CONTRACT.md §C·Comprobador.
"""

from __future__ import annotations

from app.schemas import ClientProfile, Extraction, Flag, FundKID, RiskProfileLimits


def check(extraction: Extraction, client: ClientProfile,
          kids: dict[str, FundKID] | None = None,
          limits: dict[int, RiskProfileLimits] | None = None) -> list[Flag]:
    """One flag per (recommendation x type) with value, limit and a Spanish explanation.

    TODO(C-04): SRI, horizon, concentration, liquidity, volatility (risk.portfolio_volatility).
    Defaults: kids=loaders.load_kids(), limits=loaders.load_risk_limits().
    """
    raise NotImplementedError("C-04: check() pendiente. Usa ACTA_FAKE_STAGES=check mientras tanto.")
