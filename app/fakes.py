"""Fixture loaders for fake mode (ACTA_FAKE_STAGES). Owner: D.

Every stage of the pipeline can be replaced by the golden demo in fixtures/demo/,
so each role can work without waiting for the others.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from app.config import ROOT
from app.schemas import (
    AnalysisResult,
    ClientProfile,
    ClientSummary,
    ConductCheck,
    Extraction,
    Flag,
    FundKID,
    RiskProfileLimits,
    SuitabilityReport,
    Transcript,
)

FIXTURES = ROOT / "fixtures" / "demo"


@cache
def _raw(name: str) -> object:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def transcript() -> Transcript:
    """Demo transcript (12 turns, 146 s)."""
    return Transcript.model_validate(_raw("transcript"))


def client() -> ClientProfile:
    """Demo client CLI-DEMO-001 (risk profile 3)."""
    return ClientProfile.model_validate(_raw("client"))


def kids() -> dict[str, FundKID]:
    """Three fictional demo funds keyed by ISIN."""
    return {k["isin"]: FundKID.model_validate(k) for k in _raw("kids")}  # type: ignore[union-attr]


def risk_limits() -> dict[int, RiskProfileLimits]:
    """Limits for risk profiles 1..5."""
    return {r["risk_profile"]: RiskProfileLimits.model_validate(r) for r in _raw("risk_limits")}  # type: ignore[union-attr]


def extraction() -> Extraction:
    """Extraction with verified evidence."""
    return Extraction.model_validate(_raw("extraction"))


def flags() -> list[Flag]:
    """Expected flags: horizon RED, volatility RED, concentration AMBER, SRI and liquidity GREEN."""
    return [Flag.model_validate(f) for f in _raw("flags")]  # type: ignore[union-attr]


def report() -> SuitabilityReport:
    """Report with 100 % coverage."""
    return SuitabilityReport.model_validate(_raw("report"))


def conduct() -> ConductCheck:
    """Conduct check: return promise and risks = breach; costs and conflicts = no evidence."""
    return ConductCheck.model_validate(_raw("conduct"))


def client_summary() -> ClientSummary:
    """Plain-language summary for the client."""
    return ClientSummary.model_validate(_raw("client_summary"))


def analysis_result() -> AnalysisResult:
    """Full result as the API and UI receive it."""
    return AnalysisResult.model_validate(_raw("analysis_result"))


def demo_audio() -> Path | None:
    """Demo clip if role C has added it (task C-06)."""
    p = ROOT / "app" / "data" / "audio" / "demo_clip.mp3"
    return p if p.exists() else None
