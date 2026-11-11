"""Suitability report drafting (MiFID II, Reg. 2017/565 art. 54.12). Owner: B. Task B-05.

Default: a deterministic template built ONLY from extraction fields and flags (CLAUDE.md §9 holds
by construction, no tokens spent). Every 'claim' sentence reuses the already verified Evidence.
Optional B-6 (`polish=True`): Claude rewrites only the `text` of claim/computed sentences; ids,
kinds, evidence, flags and status come from the template. Each rewrite is checked by code (same
numbers, same negations, no new «idónea») and rejected sentence by sentence if it fails.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from pydantic import BaseModel

from app.config import Settings, get_settings
from app.engine.citations import coverage
from app.schemas import (
    ClientProfile,
    Evidence,
    Extraction,
    Flag,
    ReportSection,
    ReportSentence,
    Severity,
    SuitabilityReport,
    Transcript,
)

SECTION_TITLES = {
    "client_situation": "Situación del cliente",
    "objectives_and_needs": "Objetivos y necesidades",
    "recommendations": "Recomendación",
    "suitability_assessment": "Evaluación de idoneidad",
    "risks_and_warnings": "Riesgos y advertencias",
    "commitments": "Compromisos",
}
log = logging.getLogger(__name__)
PROMPT = Path(__file__).resolve().parent / "prompts" / "report.md"
PROFILES = {1: "conservador", 2: "moderado-conservador", 3: "moderado", 4: "dinámico", 5: "agresivo"}
ACTIONS = {"buy": "invertir", "sell": "vender", "switch": "traspasar", "hold": "mantener"}


def eur(x: float) -> str:
    """20000 -> '20 000 €'."""
    return f"{x:,.0f}".replace(",", " ") + " €"


def _s(text: str) -> str:
    """Strip trailing punctuation so the template can add its own full stop."""
    return text.strip().rstrip(".;: ")


def _lower_first(text: str) -> str:
    """'El asesor…' -> 'el asesor…' after a colon; leaves acronyms ('ETF…', 'RV…') alone."""
    if len(text) > 1 and text[0].isupper() and text[1].islower():
        return text[0].lower() + text[1:]
    return text


class _Builder:
    def __init__(self) -> None:
        self.n = 0

    def _id(self) -> str:
        self.n += 1
        return f"p{self.n}"

    def claim(self, text: str, evidence: list[Evidence]) -> ReportSentence:
        ok = any(e.verified for e in evidence)
        return ReportSentence(id=self._id(), text=text, kind="claim", evidence=evidence,
                              status="supported" if ok else "no_evidence")

    def computed(self, text: str, flags: list[Flag]) -> ReportSentence:
        evs = [e for f in flags for e in f.evidence if e.verified]
        return ReportSentence(id=self._id(), text=text, kind="computed", evidence=evs,
                              flag_ids=[f.id for f in flags], status="supported" if flags else "no_evidence")

    def boilerplate(self, text: str) -> ReportSentence:
        return ReportSentence(id=self._id(), text=text, kind="boilerplate", status="supported")


def draft(extraction: Extraction, flags: list[Flag], client: ClientProfile, transcript: Transcript,
          *, advisor_name: str, meeting_date: str, polish: bool = False,
          settings: Settings | None = None) -> SuitabilityReport:
    """Six sections written only from extraction fields and flags; claims reuse verified Evidence."""
    b = _Builder()
    ext = extraction

    situation = [b.boilerplate(f"{client.name}: perfil de riesgo {PROFILES.get(client.risk_profile, '?')} "
                               f"({client.risk_profile}/5) según el último test de idoneidad.")]
    situation += [b.claim(f"{_s(c.description)}.", c.evidence) for c in ext.circumstance_changes]
    if not ext.circumstance_changes:
        situation.append(b.boilerplate("No se declararon cambios de circunstancias en la reunión."))

    needs = [b.claim(f"{_s(n.description)}" + (f" (aprox. {eur(n.amount_eur)})" if n.amount_eur else "") + ".",
                     n.evidence)
             for n in ext.stated_needs] or [b.boilerplate("No se declararon necesidades u objetivos nuevos.")]

    recs = []
    for r in ext.recommendations:
        amount = f"{eur(r.amount_eur)} " if r.amount_eur else ""
        why = f" Motivo expuesto: {_lower_first(_s(r.rationale))}." if r.rationale else ""
        recs.append(b.claim(f"El asesor recomienda {ACTIONS[r.action]} {amount}en {_s(r.product_name)}.{why}", r.evidence))
    if not recs:
        recs = [b.boilerplate("No se formuló ninguna recomendación en la reunión.")]

    order = {Severity.RED: 0, Severity.AMBER: 1, Severity.GREEN: 2}
    assessment = [b.computed(f"{f.title}: {f.explanation}.", [f]) for f in sorted(flags, key=lambda f: order[f.severity])]
    if not assessment:
        assessment = [b.boilerplate("No hay recomendaciones que evaluar.")]

    red = [f for f in flags if f.severity == Severity.RED]
    amber = [f for f in flags if f.severity == Severity.AMBER]
    if red:
        verdict = b.computed("Con la información disponible, la recomendación NO es idónea para el perfil del cliente: "
                             + "; ".join(f.title.lower() for f in red) + ". Debe revisarse antes de ejecutarse.", red)
    elif amber:
        verdict = b.computed("La recomendación es idónea con advertencias: "
                             + "; ".join(f.title.lower() for f in amber) + ".", amber)
    else:
        verdict = b.computed("La recomendación es coherente con el perfil del cliente según los cálculos realizados.", flags)
    risks = [verdict, b.boilerplate("Borrador generado automáticamente a partir de la grabación; "
                                    "requiere la revisión y firma del asesor.")]

    commitments = [b.claim(f"{_s(c.description)}" + (f" ({c.due})" if c.due else "") + ".", c.evidence)
                   for c in ext.commitments] or [b.boilerplate("No se registraron compromisos.")]

    sections = [ReportSection(key=k, title=SECTION_TITLES[k], sentences=s) for k, s in (
        ("client_situation", situation), ("objectives_and_needs", needs), ("recommendations", recs),
        ("suitability_assessment", assessment), ("risks_and_warnings", risks), ("commitments", commitments))]
    report = SuitabilityReport(client_id=client.client_id, client_name=client.name, advisor_name=advisor_name,
                               meeting_date=meeting_date, sections=sections, coverage_pct=100.0, model="plantilla")
    report = report.model_copy(update={"coverage_pct": coverage(report)})
    return _polish(report, settings or get_settings()) if polish else report


# --------------------------------------------------------------------------- B-6: optional LLM rewrite
class _Rewrite(BaseModel):
    id: str
    text: str


class _Rewrites(BaseModel):
    sentences: list[_Rewrite]


_NEGATIONS = ("no", "sin", "nunca", "ni")


def _numbers(text: str) -> list[str]:
    """Numbers as digit strings, ignoring thousands separators: '20 000 €' -> ['20000']."""
    found = re.findall(r"\d{1,3}(?:[ . ]\d{3})+(?:,\d+)?|\d+(?:,\d+)?", text)
    return sorted(re.sub(r"[ . ]", "", m) for m in found)


def _words(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def safe_rewrite(original: str, new: str) -> bool:
    """True if `new` keeps the numbers, negations and the «idónea» verdict of `original`."""
    if not new.strip() or len(new) > 2 * len(original) + 80:
        return False
    if _numbers(original) != _numbers(new):
        return False
    ow, nw = _words(original), _words(new)
    if any(w in ow and w not in nw for w in _NEGATIONS):
        return False
    return ("idónea" in ow) == ("idónea" in nw) and ("idóneo" in ow) == ("idóneo" in nw)


def _polish(report: SuitabilityReport, s: Settings) -> SuitabilityReport:
    """Let Claude rephrase claim/computed sentences; keep the template wherever a rewrite is unsafe."""
    from app.engine.llm import complete_json

    todo = [{"id": st.id, "section": sec.title, "text": st.text}
            for sec in report.sections for st in sec.sentences if st.kind != "boilerplate"]
    if not todo:
        return report
    try:
        out = complete_json(PROMPT.read_text(encoding="utf-8"),
                            "FRASES:\n" + json.dumps(todo, ensure_ascii=False, indent=1),
                            _Rewrites, max_tokens=4000, settings=s)
    except Exception as e:  # never break the report because of the LLM
        log.warning("redacción con Claude no disponible, se usa la plantilla: %s", e)
        return report
    new = {r.id: r.text.strip() for r in out.sentences}
    rejected = 0
    sections = []
    for sec in report.sections:
        sents = []
        for st in sec.sentences:
            cand = new.get(st.id)
            if st.kind != "boilerplate" and cand and cand != st.text:
                if safe_rewrite(st.text, cand):
                    st = st.model_copy(update={"text": cand})
                else:
                    rejected += 1
                    log.warning("frase %s: reescritura descartada (cambia cifras, negaciones o veredicto)", st.id)
            sents.append(st)
        sections.append(sec.model_copy(update={"sentences": sents}))
    log.info("informe redactado con Claude: %d frases, %d descartadas", len(todo), rejected)
    return report.model_copy(update={"sections": sections, "model": f"plantilla+{s.anthropic_model}"})
