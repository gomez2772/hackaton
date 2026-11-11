"""Plain-language summary for the client (contract 1.1). Owner: B. Task B-2."""

from __future__ import annotations

from app.config import Settings, get_settings
from app.engine.llm import complete_json, render_transcript
from app.schemas import ClientSummary, Extraction, Transcript

SYSTEM = """Redactas para el CLIENTE un resumen breve, en español llano y tuteando, de su reunión
con el asesor: qué contó, qué le propuso su asesor y los próximos pasos. Máximo 5 `points` y 3
`next_steps`. Sin jerga, sin valoraciones, sin estados de ánimo y sin datos que no se dijeron.
Nunca repitas promesas de rentabilidad ni frases de que no hay riesgo, aunque se dijeran.
Voz única y coherente: no hables en primera persona («me contaste», «nos dijiste»); usa «En la
reunión contaste…», «Tu asesor te propuso…», «Recibirás…». Verbos de lo propuesto en pasado.
Importes con el formato «20 000 €». Cada frase lleva en `evidence` una cita COPIADA LITERALMENTE
de la transcripción (de un solo turno, 4–15 palabras) que contenga el dato principal de la frase
(la cifra, el plazo o el producto); deja segment_id, start y end a null y verified a false.
`title`: «Resumen de tu reunión»."""


def summarize(transcript: Transcript, extraction: Extraction, *,
              settings: Settings | None = None) -> ClientSummary:
    """≤ 5 points and ≤ 3 next steps, each with a literal quote (validated later by the pipeline)."""
    s = settings or get_settings()
    user = (
        f"DATOS EXTRAÍDOS:\n{extraction.model_dump_json(exclude={'speaker_roles'})}\n\n"
        f"TRANSCRIPCIÓN:\n{render_transcript(transcript)}"
    )
    out = complete_json(SYSTEM, user, ClientSummary, effort="low", settings=s)
    return out.model_copy(update={"model": s.anthropic_model,
                                  "points": out.points[:5], "next_steps": out.next_steps[:3]})
