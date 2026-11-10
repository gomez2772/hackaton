"""Acta data contract. FROZEN: changes only via PR labelled `contrato` (see CLAUDE.md §2).

Every object that travels between modules is defined here. Modules exchange these
models, never loose dicts. Times are seconds from the start of the audio.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"


# --------------------------------------------------------------------------- audio
class Role(str, Enum):
    ADVISOR = "advisor"
    CLIENT = "client"
    UNKNOWN = "unknown"


class Word(BaseModel):
    text: str
    start: float
    end: float
    speaker_id: str


class Segment(BaseModel):
    """A contiguous turn of one speaker."""

    id: str = Field(description="Stable id, e.g. 's0007'")
    speaker_id: str = Field(description="Raw STT label, e.g. 'speaker_0'")
    role: Role = Role.UNKNOWN
    start: float
    end: float
    text: str
    words: list[Word] = Field(default_factory=list)


class Transcript(BaseModel):
    audio_id: str = Field(description="sha256 of the audio bytes (first 16 hex chars)")
    language: str = "es"
    duration_s: float
    segments: list[Segment]
    stt_provider: Literal["elevenlabs", "whisper", "fixture"]


# --------------------------------------------------------------------------- inputs
class Holding(BaseModel):
    isin: str
    name: str
    amount_eur: float


class ClientProfile(BaseModel):
    client_id: str
    name: str
    risk_profile: int = Field(ge=1, le=5, description="MiFID suitability profile 1 (conservative) .. 5")
    horizon_years: float | None = None
    liquidity_need_eur: float | None = None
    portfolio: list[Holding] = Field(default_factory=list)
    synthetic: bool = True


class FundKID(BaseModel):
    isin: str
    name: str
    manager: str
    asset_class: str
    sri: int = Field(ge=1, le=7)
    recommended_holding_years: float
    ongoing_costs_pct: float
    liquidity_days: int = Field(description="Settlement days to cash (T+n)")
    proxy_ticker: str = Field(description="ETF used to estimate volatility/covariance")
    source_url: str
    kid_date: str


class RiskProfileLimits(BaseModel):
    risk_profile: int = Field(ge=1, le=5)
    label: str
    max_sri: int
    max_volatility_pct: float
    max_single_position_pct: float = 25.0


# --------------------------------------------------------------------------- evidence
class Evidence(BaseModel):
    """A literal quote from the transcript. Located and verified by engine.citations."""

    quote: str
    segment_id: str | None = None
    start: float | None = None
    end: float | None = None
    verified: bool = False


# --------------------------------------------------------------------------- extraction
class CircumstanceChange(BaseModel):
    id: str
    field: Literal[
        "horizon", "income", "family", "liquidity_need", "risk_tolerance",
        "knowledge_experience", "financial_situation", "other",
    ]
    description: str
    new_value: str | None = None
    evidence: list[Evidence]


class StatedNeed(BaseModel):
    id: str
    kind: Literal["liquidity", "horizon", "income", "capital_preservation", "growth", "esg", "other"]
    description: str
    amount_eur: float | None = None
    horizon_years: float | None = None
    evidence: list[Evidence]


class Recommendation(BaseModel):
    id: str
    product_name: str
    isin: str | None = Field(default=None, description="Resolved against the KID catalogue if possible")
    action: Literal["buy", "sell", "switch", "hold"]
    amount_eur: float | None = None
    rationale: str
    evidence: list[Evidence]


class Commitment(BaseModel):
    id: str
    who: Role
    description: str
    due: str | None = None
    evidence: list[Evidence]


class Extraction(BaseModel):
    circumstance_changes: list[CircumstanceChange] = Field(default_factory=list)
    stated_needs: list[StatedNeed] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    commitments: list[Commitment] = Field(default_factory=list)
    speaker_roles: dict[str, Role] = Field(default_factory=dict, description="speaker_id -> role")


# --------------------------------------------------------------------------- checker
class Severity(str, Enum):
    RED = "red"
    AMBER = "amber"
    GREEN = "green"


class FlagType(str, Enum):
    SRI = "sri"
    HORIZON = "horizon"
    CONCENTRATION = "concentration"
    LIQUIDITY = "liquidity"
    VOLATILITY = "volatility"


class Flag(BaseModel):
    id: str
    type: FlagType
    severity: Severity
    recommendation_id: str | None = None
    title: str = Field(description="Short Spanish label, e.g. 'Horizonte insuficiente'")
    explanation: str = Field(description="Visible computation, e.g. 'horizonte KID 5 años > 3 años declarados'")
    value: float | None = None
    limit: float | None = None
    unit: str = ""
    evidence: list[Evidence] = Field(default_factory=list)


# --------------------------------------------------------------------------- report
class ReportSentence(BaseModel):
    id: str
    text: str
    kind: Literal["claim", "computed", "boilerplate"] = Field(
        description="claim: fact about the client, needs a verified quote (counts for coverage); "
        "computed: derived from checker flags, needs flag_ids; boilerplate: fixed regulatory text"
    )
    evidence: list[Evidence] = Field(default_factory=list)
    flag_ids: list[str] = Field(default_factory=list)
    status: Literal["supported", "no_evidence"] = "no_evidence"


ReportSectionKey = Literal[
    "client_situation", "objectives_and_needs", "recommendations",
    "suitability_assessment", "risks_and_warnings", "commitments",
]


class ReportSection(BaseModel):
    key: ReportSectionKey
    title: str
    sentences: list[ReportSentence]


class SuitabilityReport(BaseModel):
    client_id: str
    client_name: str
    advisor_name: str
    meeting_date: str
    sections: list[ReportSection]
    coverage_pct: float = Field(ge=0, le=100, description="% of claim sentences with verified evidence")
    model: str
    template_mode: bool = Field(default=False, description="True if the LLM failed and fields are empty")


# --------------------------------------------------------------------------- result
class StageTiming(BaseModel):
    stage: Literal["stt", "extract", "validate", "check", "report"]
    seconds: float
    fake: bool = False


class AnalysisResult(BaseModel):
    schema_version: str = SCHEMA_VERSION
    analysis_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    client: ClientProfile
    transcript: Transcript
    extraction: Extraction
    flags: list[Flag]
    report: SuitabilityReport
    timings: list[StageTiming] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
