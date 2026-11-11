"""Report exporters: PDF, DOCX, Markdown, HTML, JSON. Owner: A. Tasks A-0 and A-4 (professional PDF).

Contract: docs/CONTRACT.md §A·Exportación. Markdown, HTML and DOCX are rendered from the same block
list (`blocks`). The PDF (`app/export/pdf.py`) is laid out from the result itself to use colour and
tables, but carries the same content; tests check both against the contract list.
"""

from __future__ import annotations

import html
import io
from typing import Literal

from app.schemas import AnalysisResult, Evidence

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


def blocks(result: AnalysisResult) -> list[Block]:
    """Format-neutral content of the export."""
    r = result.report
    out: list[Block] = [
        ("h1", f"Informe de idoneidad · {r.client_name}"),
        ("p", f"Asesor: {r.advisor_name} · Fecha: {r.meeting_date} · Análisis: {result.analysis_id}"),
        ("p", f"Cobertura de evidencia: {r.coverage_pct:.0f} %" + (" · MODO PLANTILLA (falló el LLM)" if r.template_mode else "")),
    ]
    for sec in r.sections:
        out.append(("h2", sec.title))
        for s in sec.sentences:
            mark = " [SIN EVIDENCIA: confirmar]" if s.status == "no_evidence" else ""
            cites = _cites(s.evidence) if s.kind == "claim" else ""
            out.append(("li", f"{s.text}{mark}" + (f" {cites}" if cites else "")))
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


def verdict(result: AnalysisResult) -> str:
    """Overall suitability label from the flags: 'No idóneo', 'Con advertencias', 'Idóneo' or 'Sin evaluar'."""
    sev = {f.severity.value for f in result.flags}
    if not sev:
        return "Sin evaluar"
    return "No idóneo" if "red" in sev else "Con advertencias" if "amber" in sev else "Idóneo"


def to_pdf(result: AnalysisResult) -> bytes:
    """Professional PDF: header band, verdict, coloured flags, cited sentences with [mm:ss], page footer."""
    from app.export.pdf import render

    return render(result)


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
