"""«¿Fue correcta la llamada?» Conduct checks of the meeting (contract 1.1). Owner: B. Task B-2.

A closed checklist evaluated by Claude with literal quotes, validated afterwards by
citations.validate (pipeline). It is a compliance aid, not legal advice.
"""

from __future__ import annotations

import json

from app.engine.llm import complete_json, render_transcript
from app.schemas import ConductCheck, ConductItem, ConductStatus, Extraction, Transcript

# (code, title, rule, what to look for). kind: "duty" (must happen) or "ban" (must not happen)
CHECKLIST: list[tuple[str, str, str, str]] = [
    ("recording_notice", "Aviso de grabación", "MiFID II art. 16.7; Reg. Del. 2017/565 art. 76",
     "duty: se informa al cliente de que la conversación se graba."),
    ("circumstances_updated", "Se actualiza la situación del cliente", "Reg. Del. 2017/565 art. 54",
     "duty: el asesor pregunta por cambios de situación, objetivos, horizonte o liquidez antes de recomendar."),
    ("return_promise", "Sin promesas de rentabilidad", "MiFID II art. 24.3",
     "ban: presentar rentabilidades como seguras o asegurar que no se perderá dinero en un producto con riesgo."),
    ("risks_explained", "Riesgos explicados", "MiFID II art. 24.4",
     "duty: se explican los riesgos del producto recomendado; es breach si el cliente dice no entender y no se le explica."),
    ("costs_disclosed", "Costes informados", "MiFID II art. 24.4.c; Reg. Del. 2017/565 art. 50",
     "duty: se mencionan los costes o comisiones del producto."),
    ("commercial_pressure", "Sin presión comercial", "MiFID II art. 24.1",
     "ban: meter prisa, ofertas que caducan, presionar para decidir en el momento."),
    ("conflicts_of_interest", "Conflictos de interés e incentivos", "MiFID II arts. 23 y 24.9",
     "duty: si hay incentivos o conflictos de interés, se comunican."),
]

SYSTEM = """Eres un revisor de cumplimiento normativo (MiFID II, España). Evalúas una reunión
asesor-cliente contra una lista cerrada de comprobaciones de conducta. Para cada una:
- status "ok": se hizo correctamente; o, si es una prohibición (ban), no se ha producido.
- status "breach": hay una cita que demuestra una conducta incorrecta.
- status "no_evidence": es una obligación (duty) de la que no se habló.
`explanation`: una frase clara en español. `evidence`: citas COPIADAS LITERALMENTE de la
transcripción (4–15 palabras, sin cambiar nada); vacía si no hay. Deja segment_id, start y end a
null y verified a false. Mantén code, title y rule exactamente como se dan y no añadas otros ítems."""


def check_conduct(transcript: Transcript, extraction: Extraction) -> ConductCheck:
    """One ConductItem per CHECKLIST code, with literal quotes (validated later by the pipeline)."""
    from app.config import get_settings

    checklist = [{"code": c, "title": t, "rule": r, "what_to_check": q} for c, t, r, q in CHECKLIST]
    user = (
        f"COMPROBACIONES:\n{json.dumps(checklist, ensure_ascii=False, indent=1)}\n\n"
        f"RECOMENDACIONES DETECTADAS:\n{extraction.model_dump_json(include={'recommendations'})}\n\n"
        f"TRANSCRIPCIÓN:\n{render_transcript(transcript)}"
    )
    result = complete_json(SYSTEM, user, ConductCheck)
    return _complete(result, get_settings().anthropic_model)


def _complete(result: ConductCheck, model: str) -> ConductCheck:
    """Keep checklist order, drop unknown codes and add missing ones as no_evidence."""
    by_code = {it.code: it for it in result.items}
    items = []
    for code, title, rule, _ in CHECKLIST:
        it = by_code.get(code) or ConductItem(code=code, title=title, rule=rule, status=ConductStatus.NO_EVIDENCE,
                                              explanation="El modelo no evaluó este punto; revisar a mano.")
        items.append(it.model_copy(update={"title": title, "rule": rule}))
    return ConductCheck(items=items, model=model)
