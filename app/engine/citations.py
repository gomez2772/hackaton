"""Code-verified traceability: every quote must exist in the transcript. Owner: B. Task B-03.

A quote is verified only if its words appear contiguously in one segment (or across two
consecutive segments) after normalization. The model never sets `verified`; this code does.
"""

from __future__ import annotations

import re
import unicodedata
from typing import TypeVar

from pydantic import BaseModel

from app.schemas import Evidence, Segment, SuitabilityReport, Transcript

M = TypeVar("M", bound=BaseModel)


def normalize(text: str) -> str:
    """Lowercase, strip accents and punctuation, collapse whitespace."""
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^\w\s]", " ", t)
    return " ".join(t.split())


def _tokens(seg: Segment) -> list[tuple[str, float, float]]:
    """(token, start, end) for a segment; word timestamps when available, else segment times."""
    if seg.words:
        return [(tok, w.start, w.end) for w in seg.words for tok in normalize(w.text).split()]
    return [(tok, seg.start, seg.end) for tok in normalize(seg.text).split()]


def _find(sub: list[str], toks: list[str]) -> int:
    n = len(sub)
    if n == 0 or n > len(toks):
        return -1
    for i in range(len(toks) - n + 1):
        if toks[i:i + n] == sub:
            return i
    return -1


def locate(quote: str, transcript: Transcript) -> Evidence:
    """Find the normalized quote in one segment or across two consecutive ones."""
    sub = normalize(quote).split()
    segs = transcript.segments
    for seg in segs:
        toks = _tokens(seg)
        pos = _find(sub, [t for t, _, _ in toks])
        if pos >= 0:
            return Evidence(quote=quote, segment_id=seg.id, start=toks[pos][1],
                            end=toks[pos + len(sub) - 1][2], verified=True)
    for a, b in zip(segs, segs[1:], strict=False):  # quote crossing a speaker turn
        toks = _tokens(a) + _tokens(b)
        pos = _find(sub, [t for t, _, _ in toks])
        if pos >= 0:
            return Evidence(quote=quote, segment_id=a.id, start=toks[pos][1],
                            end=toks[pos + len(sub) - 1][2], verified=True)
    return Evidence(quote=quote, verified=False)


def validate(extraction: M, transcript: Transcript) -> M:
    """Copy of `extraction` (or any model, e.g. ConductCheck) with every Evidence located and `verified` set."""
    out = extraction.model_copy(deep=True)
    _walk(out, transcript)
    return out


def _walk(obj: object, tr: Transcript) -> None:
    if isinstance(obj, BaseModel):
        for name in type(obj).model_fields:
            value = getattr(obj, name)
            if name == "evidence" and isinstance(value, list):
                setattr(obj, name, [locate(e.quote, tr) for e in value])
            else:
                _walk(value, tr)
    elif isinstance(obj, list):
        for v in obj:
            _walk(v, tr)


def coverage(report: SuitabilityReport) -> float:
    """Percentage (0-100) of kind='claim' sentences with at least one verified evidence."""
    claims = [s for sec in report.sections for s in sec.sentences if s.kind == "claim"]
    if not claims:
        return 100.0
    ok = sum(1 for s in claims if any(e.verified for e in s.evidence))
    return round(100.0 * ok / len(claims), 1)
