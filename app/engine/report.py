"""Suitability report drafting (MiFID II, Reg. 2017/565 art. 54.12). Owner: B. Task B-05."""

from __future__ import annotations

from app.schemas import ClientProfile, Extraction, Flag, SuitabilityReport, Transcript

SECTION_TITLES = {
    "client_situation": "Situación del cliente",
    "objectives_and_needs": "Objetivos y necesidades",
    "recommendations": "Recomendación",
    "suitability_assessment": "Evaluación de idoneidad",
    "risks_and_warnings": "Riesgos y advertencias",
    "commitments": "Compromisos",
}


def draft(extraction: Extraction, flags: list[Flag], client: ClientProfile, transcript: Transcript,
          *, advisor_name: str, meeting_date: str) -> SuitabilityReport:
    """Six sections written only from extraction fields and flags; claims reuse verified Evidence.

    TODO(B-05): prompts/report.md; the LLM returns sentences referencing extraction ids
    (e.g. "n2", "r1") and flag ids; code attaches the Evidence objects (never the LLM);
    compute coverage with citations.coverage(); on LLMError -> template_mode=True.
    """
    raise NotImplementedError("B-05: draft() pendiente. Usa ACTA_FAKE_STAGES=report mientras tanto.")
