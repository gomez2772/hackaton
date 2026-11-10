"""Suitability report drafting (MiFID II, Reg. 2017/565 art. 54.12). Owner: B. Task B-05.

Default: a deterministic template built ONLY from extraction fields and flags (CLAUDE.md §9 holds
by construction, no tokens spent). Every 'claim' sentence reuses the already verified Evidence.
Optional B-6: let Claude rephrase on top of this template, never adding facts.
"""

from __future__ import annotations

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
PROFILES = {1: "conservador", 2: "moderado-conservador", 3: "moderado", 4: "dinámico", 5: "agresivo"}
ACTIONS = {"buy": "invertir", "sell": "vender", "switch": "traspasar", "hold": "mantener"}


def eur(x: float) -> str:
    """20000 -> '20 000 €'."""
    return f"{x:,.0f}".replace(",", " ") + " €"


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
          *, advisor_name: str, meeting_date: str) -> SuitabilityReport:
    """Six sections written only from extraction fields and flags; claims reuse verified Evidence."""
    b = _Builder()
    ext = extraction

    situation = [b.boilerplate(f"{client.name}: perfil de riesgo {PROFILES.get(client.risk_profile, '?')} "
                               f"({client.risk_profile}/5) según el último test de idoneidad.")]
    situation += [b.claim(f"{c.description}.", c.evidence) for c in ext.circumstance_changes]
    if not ext.circumstance_changes:
        situation.append(b.boilerplate("No se declararon cambios de circunstancias en la reunión."))

    needs = [b.claim(f"{n.description}" + (f" (aprox. {eur(n.amount_eur)})" if n.amount_eur else "") + ".", n.evidence)
             for n in ext.stated_needs] or [b.boilerplate("No se declararon necesidades u objetivos nuevos.")]

    recs = []
    for r in ext.recommendations:
        amount = f"{eur(r.amount_eur)} " if r.amount_eur else ""
        why = f" Motivo expuesto: {r.rationale}." if r.rationale else ""
        recs.append(b.claim(f"El asesor recomienda {ACTIONS[r.action]} {amount}en {r.product_name}.{why}", r.evidence))
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

    commitments = [b.claim(f"{c.description}" + (f" ({c.due})" if c.due else "") + ".", c.evidence)
                   for c in ext.commitments] or [b.boilerplate("No se registraron compromisos.")]

    sections = [ReportSection(key=k, title=SECTION_TITLES[k], sentences=s) for k, s in (
        ("client_situation", situation), ("objectives_and_needs", needs), ("recommendations", recs),
        ("suitability_assessment", assessment), ("risks_and_warnings", risks), ("commitments", commitments))]
    report = SuitabilityReport(client_id=client.client_id, client_name=client.name, advisor_name=advisor_name,
                               meeting_date=meeting_date, sections=sections, coverage_pct=100.0, model="plantilla")
    return report.model_copy(update={"coverage_pct": coverage(report)})
