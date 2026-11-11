"""Highlight cited fragments in the transcript by type, with a legend (A-3). Owner: A.

Pure helpers (no Streamlit). Each verified Evidence of the extraction and the conduct check is located
inside its segment (accent-, case- and punctuation-tolerant) and painted with the colour of its type.
If a quote cannot be located inside the segment (e.g. it spans two segments) the whole segment is painted.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.schemas import AnalysisResult, Evidence


@dataclass(frozen=True)
class Kind:
    key: str
    label: str
    color: str  # Streamlit markdown colour: blue, green, orange, red, violet, gray


# Order = priority when two cited fragments overlap (first wins the colour; every type still gets its badge).
KINDS: tuple[Kind, ...] = (
    Kind("conduct_breach", "Conducta: incumplimiento", "red"),
    Kind("recommendation", "Recomendación", "violet"),
    Kind("circumstance", "Circunstancia", "blue"),
    Kind("need", "Necesidad", "green"),
    Kind("commitment", "Compromiso", "orange"),
    Kind("conduct_ok", "Conducta: correcta", "gray"),
)
BY_KEY = {k.key: k for k in KINDS}
_PRIORITY = {k.key: i for i, k in enumerate(KINDS)}


@dataclass(frozen=True)
class Cite:
    kind: str
    item_id: str
    evidence: Evidence


def cites(result: AnalysisResult) -> list[Cite]:
    """Every verified quote of the analysis, tagged with its type."""
    ex = result.extraction
    groups = [("circumstance", ex.circumstance_changes), ("need", ex.stated_needs),
              ("recommendation", ex.recommendations), ("commitment", ex.commitments)]
    out = [Cite(kind, item.id, e) for kind, items in groups for item in items for e in item.evidence if e.verified]
    if result.conduct:
        for item in result.conduct.items:
            kind = "conduct_breach" if item.status.value == "breach" else "conduct_ok"
            out += [Cite(kind, item.code, e) for e in item.evidence if e.verified]
    return out


def _fold(text: str) -> str:
    """Lower-case and strip accents char by char, keeping the length (so indices map 1:1)."""
    return "".join(unicodedata.normalize("NFD", ch)[0].lower() for ch in text)


def find_span(text: str, quote: str) -> tuple[int, int] | None:
    """Where `quote` is inside `text`, ignoring case, accents and punctuation/spacing differences."""
    words = re.findall(r"\w+", _fold(quote))
    if not words:
        return None
    m = re.search(r"\b" + r"\W+".join(map(re.escape, words)) + r"\b", _fold(text))
    return (m.start(), m.end()) if m else None


def segment_spans(text: str, segment_cites: list[Cite]) -> list[tuple[int, int, str]]:
    """Non-overlapping (start, end, kind) runs; overlaps go to the higher-priority kind."""
    paint: list[str | None] = [None] * len(text)
    for c in sorted(segment_cites, key=lambda c: -_PRIORITY[c.kind]):  # low priority first, high overwrites
        start, end = find_span(text, c.evidence.quote) or (0, len(text))
        for i in range(start, end):
            paint[i] = c.kind
    runs: list[tuple[int, int, str]] = []
    for i, k in enumerate(paint):
        if k is None:
            continue
        if runs and runs[-1][1] == i and runs[-1][2] == k:
            runs[-1] = (runs[-1][0], i + 1, k)
        else:
            runs.append((i, i + 1, k))
    return runs


_MD_SPECIAL = re.compile(r"([\\`*_\[\]$~<>#|])")


def _md(text: str) -> str:
    return _MD_SPECIAL.sub(r"\\\1", text)


def render_segment(text: str, segment_cites: list[Cite]) -> str:
    """Streamlit markdown of the segment text with cited fragments highlighted, plus one badge per type."""
    out, pos = [], 0
    for start, end, kind in segment_spans(text, segment_cites):
        out.append(_md(text[pos:start]))
        out.append(f":{BY_KEY[kind].color}-background[{_md(text[start:end])}]")
        pos = end
    out.append(_md(text[pos:]))
    kinds = sorted({c.kind for c in segment_cites}, key=_PRIORITY.__getitem__)
    badges = " ".join(f":{BY_KEY[k].color}-badge[{BY_KEY[k].label}]" for k in kinds)
    return "".join(out) + (f"  {badges}" if badges else "")


def by_segment(result: AnalysisResult) -> dict[str, list[Cite]]:
    """Cites grouped by segment id."""
    out: dict[str, list[Cite]] = {}
    for c in cites(result):
        if c.evidence.segment_id:
            out.setdefault(c.evidence.segment_id, []).append(c)
    return out


def legend(result: AnalysisResult) -> str:
    """One badge per type with how many quotes of that type there are (types with none are omitted)."""
    counts: dict[str, int] = {}
    for c in cites(result):
        counts[c.kind] = counts.get(c.kind, 0) + 1
    return " ".join(f":{k.color}-badge[{k.label} · {counts[k.key]}]" for k in KINDS if k.key in counts)
