"""Code-verified traceability: every quote must exist in the transcript. Owner: B. Task B-03."""

from __future__ import annotations

from app.schemas import Evidence, Extraction, SuitabilityReport, Transcript


def normalize(text: str) -> str:
    """Lowercase, strip accents and punctuation, collapse whitespace."""
    raise NotImplementedError("B-03")


def locate(quote: str, transcript: Transcript) -> Evidence:
    """Find the normalized quote in one segment or across two consecutive ones."""
    raise NotImplementedError("B-03")


def validate(extraction: Extraction, transcript: Transcript) -> Extraction:
    """Copy of `extraction` with every Evidence located and `verified` set."""
    raise NotImplementedError("B-03")


def coverage(report: SuitabilityReport) -> float:
    """Percentage (0-100) of kind='claim' sentences with at least one verified evidence."""
    claims = [s for sec in report.sections for s in sec.sentences if s.kind == "claim"]
    if not claims:
        return 100.0
    ok = sum(1 for s in claims if any(e.verified for e in s.evidence))
    return round(100.0 * ok / len(claims), 1)
