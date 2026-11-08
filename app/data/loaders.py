"""Loaders for reference data. Owner: C. Tasks C-02, C-03, C-05.

Until the real files exist, each loader falls back to fixtures/demo/ with a warning,
so the rest of the team is never blocked.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from app import fakes
from app.schemas import ClientProfile, FundKID, RiskProfileLimits

log = logging.getLogger(__name__)
DATA = Path(__file__).resolve().parent


def load_kids() -> dict[str, FundKID]:
    """KID catalogue keyed by ISIN (app/data/kids.json)."""
    p = DATA / "kids.json"
    if not p.exists():
        log.warning("app/data/kids.json no existe todavía (C-02); uso los fondos demo.")
        return fakes.kids()
    return {k["isin"]: FundKID.model_validate(k) for k in json.loads(p.read_text(encoding="utf-8"))}


def load_risk_limits() -> dict[int, RiskProfileLimits]:
    """Limits per risk profile 1..5 (app/data/risk_limits.json)."""
    p = DATA / "risk_limits.json"
    if not p.exists():
        log.warning("app/data/risk_limits.json no existe todavía (C-03); uso los límites demo.")
        return fakes.risk_limits()
    return {r["risk_profile"]: RiskProfileLimits.model_validate(r) for r in json.loads(p.read_text(encoding="utf-8"))}


def list_clients() -> list[ClientProfile]:
    """All synthetic clients (app/data/clients/*.json), demo client always included."""
    folder = DATA / "clients"
    clients = [ClientProfile.model_validate_json(f.read_text(encoding="utf-8")) for f in sorted(folder.glob("*.json"))]
    if not any(c.client_id == "CLI-DEMO-001" for c in clients):
        clients.insert(0, fakes.client())
    return clients


def load_client(client_id: str) -> ClientProfile:
    """One client by id; KeyError if unknown."""
    for c in list_clients():
        if c.client_id == client_id:
            return c
    raise KeyError(client_id)


def load_returns(tickers: list[str]) -> pd.DataFrame:
    """Daily returns (3 years) for proxy tickers from app/data/prices/<ticker>.csv.

    TODO(C-05): read CSVs (date, close), pct_change, inner-join on date.
    """
    raise NotImplementedError("C-05: load_returns() pendiente.")
