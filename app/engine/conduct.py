"""«¿Fue correcta la llamada?» Conduct checks of the meeting (contract 1.1). Owner: B. Task B-2.

A closed checklist evaluated by Claude with literal quotes, validated afterwards by
citations.validate (pipeline). It is a compliance aid, not legal advice.
"""

from __future__ import annotations

import json
import logging
import re

from app.config import Settings, get_settings
from app.engine.llm import complete_json, render_transcript
from app.schemas import ConductCheck, ConductItem, ConductStatus, Extraction, Transcript

log = logging.getLogger(__name__)

# (code, title, rule, what to look for). kind: "duty" (must happen) or "ban" (must not happen)
CHECKLIST: list[tuple[str, str, str, str]] = [
    ("recording_notice", "Aviso de grabación", "MiFID II art. 16.7; Reg. Del. 2017/565 art. 76",
     "duty: se informa al cliente de que la conversación se graba."),
    ("circumstances_updated", "Se actualiza la situación del cliente", "MiFID II art. 25.2; Reg. Del. 2017/565 arts. 54 y 55",
     "duty: el asesor pregunta por cambios de situación, objetivos, horizonte o liquidez antes de recomendar."),
    ("return_promise", "Sin promesas de rentabilidad", "MiFID II art. 24.3; Reg. Del. 2017/565 art. 44",
     "ban: presentar rentabilidades como seguras o asegurar que no se perderá dinero en un producto con riesgo."),
    ("risks_explained", "Riesgos explicados", "MiFID II art. 24.4; Reg. Del. 2017/565 art. 48",
     "duty: se explican los riesgos del producto recomendado; es breach si el cliente dice no entender y no se le explica."),
    ("costs_disclosed", "Costes informados", "MiFID II art. 24.4.c; Reg. Del. 2017/565 art. 50",
     "duty: se mencionan los costes o comisiones del producto."),
    ("commercial_pressure", "Sin presión comercial", "MiFID II art. 24.1",
     "ban: meter prisa, ofertas que caducan, presionar para decidir en el momento."),
    ("conflicts_of_interest", "Conflictos de interés e incentivos", "MiFID II arts. 23 y 24.9",
     "duty: si hay incentivos o conflictos de interés, se comunican."),
]

# Ids of C's local checklist (app/data/normativa/checklist_mifid.json) behind each check. Set by
# code, never by the model; shown appended to `rule`. Checks the checklist doesn't cover have none.
REQUIREMENT_IDS: dict[str, list[str]] = {
    "recording_notice": ["REG-01"],
    "circumstances_updated": ["KYC-01", "KYC-02", "KYC-05"],
    "risks_explained": ["AJU-05"],
    "costs_disclosed": ["COS-01"],
}

SYSTEM = """Eres un revisor de cumplimiento normativo (MiFID II, España). Evalúas una reunión
asesor-cliente contra una lista cerrada de comprobaciones de conducta. Cada comprobación es una
obligación (duty: debe ocurrir) o una prohibición (ban: no debe ocurrir). Para cada una:
- status "ok": la obligación se cumplió (cita que lo demuestra) o la prohibición no se ha producido.
  En una prohibición cumplida, si el asesor lo deja claro con una frase («no le puedo asegurar
  ninguna rentabilidad», «no hay ninguna prisa», «no recibimos incentivos»), cítala; si no, evidence
  vacía.
- status "breach": hay una conducta incorrecta. La evidence DEBE incluir TODAS las frases del
  asesor que la demuestran (hasta 3: cada promesa, cada frase de presión, o su respuesta evasiva
  tras una duda del cliente, como «no se preocupe…») y, si ayuda, la frase del cliente que da
  contexto.
- status "no_evidence": es una obligación (duty) de la que no se habló.
No des "ok" a una obligación sin una cita que lo demuestre.
Juzga con la normativa de <normativa> y el <checklist>; en `explanation` puedes mencionar el id del
checklist que aplica (p. ej. REG-01), nunca uno que no exista.
`explanation`: una frase clara en español, sin juicios jurídicos definitivos. `evidence`: citas
COPIADAS LITERALMENTE de la transcripción, de un solo turno, entre 4 y 15 palabras, sin cambiar
nada (ni números, ni signos). Deja segment_id, start y end a null y verified a false. Mantén
code, title y rule exactamente como se dan, un ítem por code, y no añadas otros."""


def check_conduct(transcript: Transcript, extraction: Extraction, *,
                  settings: Settings | None = None) -> ConductCheck:
    """One ConductItem per CHECKLIST code, with literal quotes (validated later by the pipeline)."""
    s = settings or get_settings()
    checklist = [{"code": c, "title": t, "rule": r, "what_to_check": q} for c, t, r, q in CHECKLIST]
    user = (
        f"COMPROBACIONES:\n{json.dumps(checklist, ensure_ascii=False, indent=1)}\n\n"
        f"RECOMENDACIONES DETECTADAS:\n{extraction.model_dump_json(include={'recommendations'})}\n\n"
        f"TRANSCRIPCIÓN:\n{render_transcript(transcript)}"
    )
    result = complete_json(SYSTEM, user, ConductCheck, effort="medium", knowledge=True, settings=s)
    return _complete(result, s.anthropic_model)


def rule_with_ids(code: str, rule: str) -> str:
    """'MiFID II art. 16.7; …' + ' · REG-01' when the local checklist covers the check."""
    ids = REQUIREMENT_IDS.get(code, [])
    return f"{rule} · {', '.join(ids)}" if ids else rule


def _strip_invalid_ids(text: str) -> str:
    """Remove checklist ids that do not exist (the model must never invent a reference)."""
    from app.data.regulation import invalid_references

    for bad in invalid_references(text):
        log.warning("conducta: referencia inexistente %s eliminada", bad)
        text = re.sub(rf"\s*\(?\b{re.escape(bad)}\b\)?", "", text)
    return text


def _complete(result: ConductCheck, model: str) -> ConductCheck:
    """Keep checklist order, drop unknown codes, add missing ones as no_evidence, set rule ids by code."""
    by_code = {it.code: it for it in result.items}
    items = []
    for code, title, rule, _ in CHECKLIST:
        it = by_code.get(code) or ConductItem(code=code, title=title, rule=rule, status=ConductStatus.NO_EVIDENCE,
                                              explanation="El modelo no evaluó este punto; revisar a mano.")
        items.append(it.model_copy(update={"title": title, "rule": rule_with_ids(code, rule),
                                           "explanation": _strip_invalid_ids(it.explanation)}))
    return ConductCheck(items=items, model=model)
