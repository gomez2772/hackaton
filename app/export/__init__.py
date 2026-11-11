"""Report exporters: PDF, DOCX, Markdown, HTML, JSON. Owner: A. Tasks A-0 and A-4 (professional PDF).

Contract: docs/CONTRACT.md §A·Exportación. Markdown, HTML and DOCX are rendered from the same block
list (`blocks`). The PDF (`app/export/pdf.py`) is laid out from the result itself to use colour and
tables, but carries the same content; tests check both against the contract list.
"""

from __future__ import annotations

import html
import io
from typing import Literal

from app.schemas import AnalysisResult, Evidence, Recommendation, ReportSentence

Format = Literal["pdf", "docx", "md", "html", "json"]

FORMATS: dict[str, str] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md": "text/markdown; charset=utf-8",
    "html": "text/html; charset=utf-8",
    "json": "application/json",
}
SEV_TXT = {"red": "ROJO", "amber": "ÁMBAR", "green": "VERDE"}
CONDUCT = {"ok": "Cumple", "breach": "NO CUMPLE", "no_evidence": "Sin evidencia"}
FOOTER = ("Borrador generado con IA a partir de la grabación; requiere revisión del asesor. "
          "Clientes, carteras y reuniones de esta demostración son sintéticos.")

Block = tuple[str, str]  # (kind, text): kind in h1, h2, p, li, small


def mmss(t: float | None) -> str:
    """64.2 -> '01:04'."""
    t = int(t or 0)
    return f"{t // 60:02d}:{t % 60:02d}"


def _cites(evs: list[Evidence]) -> str:
    ok = [e for e in evs if e.verified]
    return " ".join(f"[{mmss(e.start)} «{e.quote}»]" for e in ok)


# ------------------------------------------------------------------ advisor confirmation of no_evidence sentences (A-6)
# The frozen schema has no "confirmed" status, and CLAUDE.md §9 forbids presenting a sentence without a quote as
# supported. So a confirmed sentence keeps status="no_evidence" and carries this suffix; exporters show it as
# «sin cita en el audio · confirmado por el asesor» instead of «SIN EVIDENCIA: confirmar».
CONFIRMED_SUFFIX = " ⟦confirmado por el asesor⟧"
CONFIRMED_LABEL = "sin cita en el audio · confirmado por el asesor"


def is_confirmed(sentence: ReportSentence) -> bool:
    """True if the advisor confirmed this no_evidence sentence (see `apply_edits`)."""
    return sentence.status == "no_evidence" and sentence.text.endswith(CONFIRMED_SUFFIX)


def sentence_text(sentence: ReportSentence) -> str:
    """Sentence text as shown to people (without the confirmation suffix)."""
    return sentence.text.removesuffix(CONFIRMED_SUFFIX)


def apply_edits(result: AnalysisResult, edits: dict[str, str]) -> AnalysisResult:
    """Copy of `result` where each no_evidence sentence id in `edits` takes the advisor's text, marked as confirmed.

    Sentences with evidence are never changed: they stay tied to the quote in the audio."""
    if not edits:
        return result
    out = result.model_copy(deep=True)
    for sec in out.report.sections:
        for s in sec.sentences:
            text = edits.get(s.id, "").strip()
            if s.status == "no_evidence" and text:
                s.text = text + CONFIRMED_SUFFIX
    return out


def blocks(result: AnalysisResult) -> list[Block]:
    """Format-neutral content of the export."""
    r = result.report
    out: list[Block] = [
        ("h1", f"Informe de idoneidad · {r.client_name}"),
        ("p", f"Asesor: {r.advisor_name} · Fecha: {r.meeting_date} · Análisis: {result.analysis_id}"),
        ("p", f"Cobertura de evidencia: {r.coverage_pct:.0f} %" + (" · MODO PLANTILLA (falló el LLM)" if r.template_mode else "")),
        ("p", f"Idoneidad: {verdict(result)}"),
    ]
    if note := unchecked_note(result):
        out.append(("p", f"ATENCIÓN: {note}"))
    for sec in r.sections:
        out.append(("h2", sec.title))
        for s in sec.sentences:
            mark = ""
            if s.status == "no_evidence":
                mark = f" [{CONFIRMED_LABEL}]" if is_confirmed(s) else " [SIN EVIDENCIA: confirmar]"
            cites = _cites(s.evidence) if s.kind == "claim" else ""
            out.append(("li", f"{sentence_text(s)}{mark}" + (f" {cites}" if cites else "")))
    out.append(("h2", "Banderas del comprobador"))
    for f in result.flags:
        out.append(("li", f"{SEV_TXT[f.severity.value]} · {f.title}: {f.explanation}"))
    if result.conduct:
        out.append(("h2", "Conducta durante la reunión"))
        for it in result.conduct.items:
            cites = _cites(it.evidence)
            out.append(("li", f"{CONDUCT[it.status.value]} · {it.title} ({it.rule}): {it.explanation}"
                        + (f" {cites}" if cites else "")))
    if result.client_summary:
        cs = result.client_summary
        out.append(("h2", f"Resumen para el cliente: {cs.title}"))
        out += [("li", p.text) for p in cs.points]
        if cs.next_steps:
            out.append(("p", "Próximos pasos:"))
            out += [("li", p.text) for p in cs.next_steps]
    out.append(("small", FOOTER))
    return out


def to_markdown(result: AnalysisResult) -> str:
    """Markdown rendering of `blocks`."""
    pre = {"h1": "# ", "h2": "\n## ", "li": "- ", "p": "", "small": "\n---\n_"}
    post = {"small": "_"}
    return "\n".join(pre[k] + t + post.get(k, "") for k, t in blocks(result)) + "\n"


def to_html(result: AnalysisResult) -> str:
    """Standalone HTML page."""
    body, in_list = [], False
    for k, t in blocks(result):
        if k == "li" and not in_list:
            body.append("<ul>")
            in_list = True
        if k != "li" and in_list:
            body.append("</ul>")
            in_list = False
        tag = {"h1": "h1", "h2": "h2", "li": "li", "p": "p", "small": "p class='small'"}[k]
        body.append(f"<{tag}>{html.escape(t)}</{tag.split()[0]}>")
    if in_list:
        body.append("</ul>")
    css = ("body{font-family:system-ui,sans-serif;max-width:820px;margin:2rem auto;padding:0 1rem;line-height:1.5}"
           "h1{font-size:1.5rem}h2{font-size:1.15rem;margin-top:1.5rem}.small{color:#666;font-size:.85rem}")
    return (f"<!doctype html><html lang='es'><meta charset='utf-8'><title>Informe de idoneidad</title>"
            f"<style>{css}</style><body>{''.join(body)}</body></html>")


def to_docx(result: AnalysisResult) -> bytes:
    """Word document."""
    from docx import Document

    doc = Document()
    for k, t in blocks(result):
        if k == "h1":
            doc.add_heading(t, level=0)
        elif k == "h2":
            doc.add_heading(t, level=1)
        elif k == "li":
            doc.add_paragraph(t, style="List Bullet")
        else:
            doc.add_paragraph(t)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def unchecked_recommendations(result: AnalysisResult) -> list[Recommendation]:
    """Recommendations the checker could not evaluate against a KID.

    CONTRACT: one flag per (recommendation × type). The SRI flag needs the product's KID, so a
    recommendation without it was skipped (e.g. no ISIN from the catalogue): its SRI, horizon and
    concentration were never checked and the analysis must not read as «Idóneo»."""
    with_sri = {f.recommendation_id for f in result.flags if f.type.value == "sri"}
    return [r for r in result.extraction.recommendations if r.id not in with_sri]


INCOMPLETE = "Comprobación incompleta"


def unchecked_note(result: AnalysisResult) -> str:
    """Sentence for people explaining which recommendations were not checked ('' if none)."""
    names = [f"«{r.product_name}»" for r in unchecked_recommendations(result)]
    if not names:
        return ""
    return (f"No se ha podido comprobar {', '.join(names)}: el producto no está en el catálogo de KID, así que "
            "no se han evaluado su SRI, su horizonte ni la concentración. El asesor debe revisarlo.")


def verdict(result: AnalysisResult) -> str:
    """Overall suitability label: 'No idóneo', 'Comprobación incompleta', 'Con advertencias', 'Idóneo' or 'Sin evaluar'."""
    sev = {f.severity.value for f in result.flags}
    if "red" in sev:
        return "No idóneo"
    if unchecked_recommendations(result):
        return INCOMPLETE
    if not sev:
        return "Sin evaluar"
    return "Con advertencias" if "amber" in sev else "Idóneo"


def to_pdf(result: AnalysisResult) -> bytes:
    """Professional PDF: header band, verdict, coloured flags, cited sentences with [mm:ss], page footer."""
    from app.export.pdf import render

    return render(result)


# ------------------------------------------------------------------ client summary (A-5)
SummaryFormat = Literal["pdf", "md", "txt"]
SUMMARY_FORMATS: dict[str, str] = {
    "pdf": "application/pdf",
    "md": "text/markdown; charset=utf-8",
    "txt": "text/plain; charset=utf-8",
}
SUMMARY_NOTE = ("Resumen preparado a partir de la grabación de nuestra reunión. "
                "Si algo no es correcto, por favor, dínoslo antes de dar ningún paso.")
SUMMARY_SYNTHETIC = "Demostración con datos sintéticos."


def first_name(full_name: str) -> str:
    """'Lucía Martín (sintético)' -> 'Lucía'."""
    return full_name.split("(")[0].split()[0] if full_name.strip() else ""


def human_date(iso: str) -> str:
    """'2026-11-10' -> '10/11/2026'; anything else is returned unchanged."""
    parts = iso.split("-")
    return f"{parts[2]}/{parts[1]}/{parts[0]}" if len(parts) == 3 and all(p.isdigit() for p in parts) else iso


def summary_text(result: AnalysisResult) -> str:
    """Plain text of the client summary, ready to paste into an email or a message."""
    cs = result.client_summary
    if cs is None:
        raise ValueError("este análisis no tiene resumen para el cliente")
    r = result.report
    name = first_name(r.client_name)
    lines = [f"Hola, {name}:" if name else "Hola:", "",
             f"{cs.title} ({human_date(r.meeting_date)})", ""]
    lines += [f"- {p.text}" for p in cs.points]
    if cs.next_steps:
        lines += ["", "Próximos pasos:"] + [f"- {p.text}" for p in cs.next_steps]
    lines += ["", SUMMARY_NOTE, "", "Un saludo,", r.advisor_name, "", f"({SUMMARY_SYNTHETIC})"]
    return "\n".join(lines) + "\n"


def summary_markdown(result: AnalysisResult) -> str:
    """Markdown version of `summary_text`."""
    cs = result.client_summary
    if cs is None:
        raise ValueError("este análisis no tiene resumen para el cliente")
    r = result.report
    name = first_name(r.client_name)
    out = [f"# {cs.title}", "", f"_Reunión del {human_date(r.meeting_date)} · tu asesor: {r.advisor_name}_", "",
           f"Hola, {name}:" if name else "Hola:", ""]
    out += [f"- {p.text}" for p in cs.points]
    if cs.next_steps:
        out += ["", "## Próximos pasos", ""] + [f"- {p.text}" for p in cs.next_steps]
    out += ["", SUMMARY_NOTE, "", "Un saludo,  ", r.advisor_name, "", "---", f"_{SUMMARY_SYNTHETIC}_"]
    return "\n".join(out) + "\n"


def export_summary(result: AnalysisResult, fmt: SummaryFormat) -> bytes:
    """Serialize only the client summary in `fmt` (to send it to the client)."""
    if fmt == "txt":
        return summary_text(result).encode("utf-8")
    if fmt == "md":
        return summary_markdown(result).encode("utf-8")
    if fmt == "pdf":
        from app.export.pdf import render_summary

        return render_summary(result)
    raise ValueError(f"formato desconocido: {fmt}")


def export(result: AnalysisResult, fmt: Format) -> bytes:
    """Serialize `result` in `fmt`."""
    if fmt == "json":
        return result.model_dump_json(indent=2).encode("utf-8")
    if fmt == "md":
        return to_markdown(result).encode("utf-8")
    if fmt == "html":
        return to_html(result).encode("utf-8")
    if fmt == "docx":
        return to_docx(result)
    if fmt == "pdf":
        return to_pdf(result)
    raise ValueError(f"formato desconocido: {fmt}")
