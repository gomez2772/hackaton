"""Quantitative suitability checker (deterministic, no LLM). Owner: C. Task C-04.

Severity rules: docs/CONTRACT.md §C·Comprobador. Percentages in 0-100, Spanish formatting.
"""

from __future__ import annotations

import logging

from app.engine.risk import approx_volatility, portfolio_volatility, resulting_portfolio
from app.schemas import (
    ClientProfile,
    Evidence,
    Extraction,
    Flag,
    FlagType,
    FundKID,
    RiskProfileLimits,
    Severity,
)

log = logging.getLogger(__name__)
RED, AMBER, GREEN = Severity.RED, Severity.AMBER, Severity.GREEN


def num(x: float, dec: int = 1) -> str:
    """16.04 -> '16,0' ; 20000 -> '20 000'."""
    if dec == 0:
        return f"{x:,.0f}".replace(",", " ")
    return f"{x:.{dec}f}".replace(".", ",")


def check(extraction: Extraction, client: ClientProfile,
          kids: dict[str, FundKID] | None = None,
          limits: dict[int, RiskProfileLimits] | None = None) -> list[Flag]:
    """One flag per (recommendation x type) with value, limit and a Spanish explanation."""
    from app.data.loaders import load_kids, load_risk_limits

    kids = kids if kids is not None else load_kids()
    limits = limits if limits is not None else load_risk_limits()
    lim = limits[client.risk_profile]
    flags: list[Flag] = []

    def add(**kw) -> None:
        flags.append(Flag(id=f"f{len(flags) + 1}", **kw))

    # horizon declared = min(stated horizon needs, profile horizon)
    hz_needs = [n for n in extraction.stated_needs if n.kind == "horizon" and n.horizon_years]
    candidates = [n.horizon_years for n in hz_needs] + ([client.horizon_years] if client.horizon_years else [])
    horizon = min(candidates) if candidates else None
    hz_ev: list[Evidence] = [e for n in hz_needs for e in n.evidence]
    preserve = any(n.kind == "capital_preservation" for n in extraction.stated_needs)
    liq_needs = [n for n in extraction.stated_needs if n.kind == "liquidity" and n.amount_eur]
    need = max([n.amount_eur for n in liq_needs] + [client.liquidity_need_eur or 0.0])
    liq_ev = [e for n in liq_needs for e in n.evidence]

    recs = [r for r in extraction.recommendations if r.action in ("buy", "switch")]
    pf = resulting_portfolio(client, extraction.recommendations, kids)
    total = sum(pf.values()) or 1.0

    for r in recs:
        kid = kids.get(r.isin or "")
        if kid is None:
            log.warning("recomendación %s sin ISIN del catálogo: no se puede comprobar", r.id)
            continue
        rid = r.id

        sev = RED if kid.sri > lim.max_sri else AMBER if (kid.sri == lim.max_sri and preserve) else GREEN
        sign = ">" if kid.sri > lim.max_sri else "≤"
        add(type=FlagType.SRI, severity=sev, recommendation_id=rid,
            title="Riesgo del producto por encima del perfil" if sev == RED else
            "Riesgo en el límite con preferencia por preservar capital" if sev == AMBER else "SRI dentro del perfil",
            explanation=f"SRI del producto {kid.sri} {sign} {lim.max_sri} máximo del perfil {client.risk_profile} ({lim.label})",
            value=kid.sri, limit=lim.max_sri, unit="SRI")

        if horizon is None:
            add(type=FlagType.HORIZON, severity=AMBER, recommendation_id=rid, title="Horizonte no declarado",
                explanation=f"El KID recomienda {num(kid.recommended_holding_years, 0)} años y no consta el horizonte del cliente",
                value=None, limit=kid.recommended_holding_years, unit="años")
        else:
            k = kid.recommended_holding_years
            sev = RED if k > horizon else AMBER if k == horizon else GREEN
            add(type=FlagType.HORIZON, severity=sev, recommendation_id=rid,
                title="Horizonte insuficiente" if sev == RED else "Horizonte justo" if sev == AMBER else "Horizonte adecuado",
                explanation=f"Horizonte recomendado KID {num(k, 0)} años {'>' if k > horizon else '≤'} "
                            f"{num(horizon, 0)} años declarados",
                value=horizon, limit=k, unit="años", evidence=hz_ev)

        w = 100 * pf.get(kid.isin, 0.0) / total
        sev = RED if w > 40 else AMBER if w > lim.max_single_position_pct else GREEN
        add(type=FlagType.CONCENTRATION, severity=sev, recommendation_id=rid,
            title="Concentración elevada" if sev != GREEN else "Concentración razonable",
            explanation=f"{kid.name} pasaría a {num(w)} % de la cartera "
                        f"{'>' if sev != GREEN else '≤'} {num(lim.max_single_position_pct)} % máximo por producto",
            value=round(w, 1), limit=lim.max_single_position_pct, unit="%")

    if recs and need > 0:
        liquid = sum(v for i, v in pf.items() if i in kids and kids[i].liquidity_days <= 3)
        sev = RED if liquid < need else AMBER if liquid < 1.2 * need else GREEN
        add(type=FlagType.LIQUIDITY, severity=sev, recommendation_id=recs[0].id,
            title="Liquidez insuficiente" if sev == RED else "Liquidez justa" if sev == AMBER else "Liquidez suficiente",
            explanation=f"Activos con liquidez ≤ T+3 tras la operación {num(liquid, 0)} € "
                        f"{'<' if liquid < need else '≥'} {num(need, 0)} € necesarios",
            value=round(liquid, 2), limit=need, unit="€", evidence=liq_ev)

    if recs:
        weights = {i: v / total for i, v in pf.items()}
        vol, method = _volatility(weights, kids)
        sev = RED if vol > lim.max_volatility_pct else AMBER if vol > 0.9 * lim.max_volatility_pct else GREEN
        add(type=FlagType.VOLATILITY, severity=sev, recommendation_id=recs[0].id,
            title="Volatilidad por encima del perfil" if sev == RED else
            "Volatilidad cerca del límite" if sev == AMBER else "Volatilidad dentro del perfil",
            explanation=f"Volatilidad anual de la cartera resultante {num(vol)} % "
                        f"{'>' if vol > lim.max_volatility_pct else '≤'} {num(lim.max_volatility_pct)} % límite del "
                        f"perfil {client.risk_profile} ({lim.label}) · {method}",
            value=round(vol, 1), limit=lim.max_volatility_pct, unit="%")
    return flags


def _volatility(weights: dict[str, float], kids: dict[str, FundKID]) -> tuple[float, str]:
    """Covariance of proxy prices if available, else SRI approximation."""
    from app.data.loaders import load_returns

    proxies = {i: kids[i].proxy_ticker for i in weights if i in kids}
    try:
        rets = load_returns(sorted(set(proxies.values())))
        by_ticker: dict[str, float] = {}
        for i, w in weights.items():
            if i in proxies:
                by_ticker[proxies[i]] = by_ticker.get(proxies[i], 0.0) + w
        return portfolio_volatility(by_ticker, rets), "covarianza de 3 años de precios"
    except (FileNotFoundError, KeyError, ValueError):
        return approx_volatility(weights, kids), "estimación por SRI"
