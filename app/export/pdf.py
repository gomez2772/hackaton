"""Professional PDF of the suitability report (A-4). Owner: A.

Layout: header band and page footer on every page («Página n de N»), verdict and key figures,
the 6 report sections with each sentence's citations as [mm:ss] «quote», sentences without
evidence highlighted in amber, colour-coded flag and conduct tables, client summary and the
synthetic-data / AI-draft disclaimer. Uses the Bitstream Vera fonts shipped with reportlab
(≤ ≥ € « » — and accents render correctly on any OS, no system fonts needed).
"""

from __future__ import annotations

import html
import io
import re
from pathlib import Path

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.export import CONDUCT, FOOTER, SEV_TXT, mmss, verdict
from app.schemas import AnalysisResult, Evidence

# ------------------------------------------------------------------ palette and fonts
NAVY = colors.HexColor("#1F3A5F")
INK = colors.HexColor("#1F2937")
GREY = colors.HexColor("#6B7280")
RULE = colors.HexColor("#D1D5DB")
SOFT = colors.HexColor("#F3F4F6")
SEV_COLOR = {"red": colors.HexColor("#B42318"), "amber": colors.HexColor("#B54708"), "green": colors.HexColor("#067647")}
SEV_SOFT = {"red": colors.HexColor("#FEE4E2"), "amber": colors.HexColor("#FEF0C7"), "green": colors.HexColor("#DCFAE6")}
CONDUCT_SEV = {"ok": "green", "breach": "red", "no_evidence": None}
VERDICT_SEV = {"No idóneo": "red", "Con advertencias": "amber", "Idóneo": "green"}

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
WIDTH = PAGE_W - 2 * MARGIN
FONT, BOLD, ITALIC = "Vera", "Vera-Bold", "Vera-Italic"


def _register_fonts() -> None:
    if FONT in pdfmetrics.getRegisteredFontNames():
        return
    d = Path(reportlab.__file__).parent / "fonts"
    for name, file in [(FONT, "Vera.ttf"), (BOLD, "VeraBd.ttf"), (ITALIC, "VeraIt.ttf"), ("Vera-BoldItalic", "VeraBI.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(d / file)))
    pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=BOLD, italic=ITALIC, boldItalic="Vera-BoldItalic")


def _styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle("base", fontName=FONT, fontSize=9.5, leading=13.5, textColor=INK)
    return {
        "title": ParagraphStyle("title", base, fontName=BOLD, fontSize=20, leading=24, textColor=NAVY),
        "subtitle": ParagraphStyle("subtitle", base, fontSize=10, textColor=GREY, spaceAfter=10),
        "h2": ParagraphStyle("h2", base, fontName=BOLD, fontSize=12.5, leading=16, textColor=NAVY,
                             spaceBefore=14, spaceAfter=5),
        "body": ParagraphStyle("body", base, spaceAfter=2),
        "missing": ParagraphStyle("missing", base, backColor=SEV_SOFT["amber"], borderPadding=(3, 4, 3, 4),
                                  spaceBefore=3, spaceAfter=5),
        "cite": ParagraphStyle("cite", base, fontName=ITALIC, fontSize=8, leading=11, textColor=GREY,
                               leftIndent=10, spaceAfter=5),
        "caption": ParagraphStyle("caption", base, fontSize=8.5, leading=11.5, textColor=GREY, spaceAfter=6),
        "cell": ParagraphStyle("cell", base, fontSize=8.5, leading=11.5),
        "cell_small": ParagraphStyle("cell_small", base, fontSize=7.5, leading=10, textColor=GREY),
        "badge": ParagraphStyle("badge", base, fontName=BOLD, fontSize=8, leading=10, textColor=colors.white,
                                alignment=TA_CENTER),
        "kpi_value": ParagraphStyle("kpi_value", base, fontName=BOLD, fontSize=15, leading=18, alignment=TA_CENTER),
        "kpi_label": ParagraphStyle("kpi_label", base, fontSize=7.5, leading=10, textColor=GREY, alignment=TA_CENTER),
        "label": ParagraphStyle("label", base, fontSize=7.5, leading=10, textColor=GREY),
        "value": ParagraphStyle("value", base, fontName=BOLD, fontSize=9.5, leading=12),
        "note": ParagraphStyle("note", base, fontSize=8, leading=11, textColor=GREY),
    }


_NBSP = " "
_THOUSANDS = re.compile(r"(?<=\d) (?=\d{3}\b)")
_UNIT = re.compile(r"(?<=\d) (?=[%€])")


def _esc(text: str) -> str:
    """Escape for reportlab's mini-HTML and keep numbers whole: '70 000 €' and '16,0 %' never wrap."""
    text = _UNIT.sub(_NBSP, _THOUSANDS.sub(_NBSP, text))
    return html.escape(text, quote=False)


def _hex(c: colors.Color) -> str:
    return c.hexval()[2:]


def _cites(evs: list[Evidence]) -> str:
    return "   ".join(f"[{mmss(e.start)}] «{_esc(e.quote)}»" for e in evs if e.verified)


# ------------------------------------------------------------------ page chrome (header, footer, page n of N)
def _canvas_class(result: AnalysisResult) -> type[rl_canvas.Canvas]:
    right = f"Informe de idoneidad · {result.report.client_name} · {result.analysis_id}"
    footer_lines = [s.strip() + "." for s in FOOTER.rstrip(".").split(". ")]

    class NumberedCanvas(rl_canvas.Canvas):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self._pages: list[dict] = []

        def showPage(self) -> None:  # noqa: N802 (reportlab API)
            self._pages.append(dict(self.__dict__))
            self._startPage()

        def save(self) -> None:
            total = len(self._pages)
            for state in self._pages:
                self.__dict__.update(state)
                self._chrome(total)
                super().showPage()
            super().save()

        def _chrome(self, total: int) -> None:
            top = PAGE_H - 11 * mm
            self.setFont(BOLD, 9)
            self.setFillColor(NAVY)
            self.drawString(MARGIN, top, "Acta")
            self.setFont(FONT, 8)
            self.setFillColor(GREY)
            self.drawString(MARGIN + pdfmetrics.stringWidth("Acta ", BOLD, 9), top, "· para GPTadvisor")
            self.drawRightString(PAGE_W - MARGIN, top, right)
            self.setStrokeColor(NAVY)
            self.setLineWidth(0.8)
            self.line(MARGIN, top - 3 * mm, PAGE_W - MARGIN, top - 3 * mm)
            self.setStrokeColor(RULE)
            self.setLineWidth(0.5)
            self.line(MARGIN, 15 * mm, PAGE_W - MARGIN, 15 * mm)
            self.setFont(FONT, 7)
            for i, line in enumerate(footer_lines):
                self.drawString(MARGIN, 11 * mm - i * 3.2 * mm, line)
            self.setFont(BOLD, 7.5)
            self.drawRightString(PAGE_W - MARGIN, 11 * mm, f"Página {self._pageNumber} de {total}")

    return NumberedCanvas


# ------------------------------------------------------------------ blocks
def _meta_table(result: AnalysisResult, s: dict[str, ParagraphStyle]) -> Table:
    r, c = result.report, result.client
    cells = [("Cliente", f"{r.client_name}"), ("Perfil de riesgo", f"{c.risk_profile} de 5"),
             ("Asesor", r.advisor_name), ("Fecha de la reunión", r.meeting_date),
             ("Análisis", result.analysis_id), ("Modelo", r.model or "—")]
    rows = [[Paragraph(_esc(k), s["label"]) for k, _ in cells[i:i + 3]] for i in range(0, 6, 3)]
    vals = [[Paragraph(_esc(v), s["value"]) for _, v in cells[i:i + 3]] for i in range(0, 6, 3)]
    t = Table([rows[0], vals[0], rows[1], vals[1]], colWidths=[WIDTH / 3] * 3)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), SOFT), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
                           ("BOTTOMPADDING", (0, 3), (-1, 3), 6), ("TOPPADDING", (0, 0), (-1, 0), 6)]))
    return t


def _kpis(result: AnalysisResult, s: dict[str, ParagraphStyle]) -> Table:
    v = verdict(result)
    reds = sum(f.severity.value == "red" for f in result.flags)
    ambers = sum(f.severity.value == "amber" for f in result.flags)
    breaches = (str(sum(it.status.value == "breach" for it in result.conduct.items))
                if result.conduct else "—")
    cover = "—" if result.report.template_mode else f"{result.report.coverage_pct:.0f} %"
    items = [(v, "Idoneidad"), (f"{reds} · {ambers}", "Alertas rojas · ámbar"),
             (breaches, "Incumplimientos de conducta"), (cover, "Cobertura de evidencia")]
    vsev = VERDICT_SEV.get(v)
    value_style = [ParagraphStyle(f"kv{i}", s["kpi_value"],
                                  textColor=colors.white if i == 0 and vsev else INK) for i in range(4)]
    t = Table([[Paragraph(_esc(val), value_style[i]) for i, (val, _) in enumerate(items)],
               [Paragraph(_esc(lab), s["kpi_label"] if i or not vsev else
                          ParagraphStyle("kl0", s["kpi_label"], textColor=colors.white))
                for i, (_, lab) in enumerate(items)]],
              colWidths=[WIDTH / 4] * 4)
    style = [("BOX", (0, 0), (-1, -1), 0.5, RULE), ("INNERGRID", (1, 0), (-1, -1), 0.5, RULE),
             ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    if vsev:
        style.append(("BACKGROUND", (0, 0), (0, -1), SEV_COLOR[vsev]))
    t.setStyle(TableStyle(style))
    return t


def _badge_table(rows: list[list], widths: list[float], badge_colors: list[colors.Color | None]) -> Table:
    t = Table(rows, colWidths=widths, repeatRows=1)
    style = [("LINEBELOW", (0, 0), (-1, 0), 0.8, NAVY), ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE),
             ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 5),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (0, 0), (-1, -1), 4)]
    for i, col in enumerate(badge_colors, start=1):
        style.append(("BACKGROUND", (0, i), (0, i), col or GREY))
        style.append(("VALIGN", (0, i), (0, i), "MIDDLE"))
    t.setStyle(TableStyle(style))
    return t


def _flags(result: AnalysisResult, s: dict[str, ParagraphStyle]) -> list:
    out: list = [Paragraph("Banderas del comprobador", s["h2"]),
                 Paragraph("Cálculo determinista (sin IA) sobre el perfil del cliente, los KID de los productos y la "
                           "cartera resultante.", s["caption"])]
    if not result.flags:
        return out + [Paragraph("No se han generado banderas: no se detectaron recomendaciones que evaluar.",
                                s["body"])]
    order = {"red": 0, "amber": 1, "green": 2}
    flags = sorted(result.flags, key=lambda f: order[f.severity.value])
    head = [Paragraph(f"<b>{h}</b>", s["cell"]) for h in ("Nivel", "Comprobación", "Cálculo", "Cita en el audio")]
    rows = [head] + [[Paragraph(SEV_TXT[f.severity.value], s["badge"]),
                      Paragraph(f"<b>{_esc(f.title)}</b>", s["cell"]),
                      Paragraph(_esc(f.explanation), s["cell"]),
                      Paragraph(_cites(f.evidence) or "—", s["cell_small"])] for f in flags]
    return out + [_badge_table(rows, [17 * mm, 38 * mm, 75 * mm, WIDTH - 130 * mm],
                               [SEV_COLOR[f.severity.value] for f in flags])]


def _conduct(result: AnalysisResult, s: dict[str, ParagraphStyle]) -> list:
    out: list = [Paragraph("Conducta durante la reunión", s["h2"]),
                 Paragraph("Ayuda para el equipo de cumplimiento; no sustituye una revisión jurídica.", s["caption"])]
    if not result.conduct:
        return out + [Paragraph("El chequeo de conducta no está disponible para este análisis.", s["body"])]
    items = result.conduct.items
    head = [Paragraph(f"<b>{h}</b>", s["cell"]) for h in ("Estado", "Comprobación", "Qué se observó")]
    rows = [head]
    for it in items:
        cites = _cites(it.evidence)
        rows.append([Paragraph(CONDUCT[it.status.value].upper(), s["badge"]),
                     Paragraph(f"<b>{_esc(it.title)}</b><br/><font size=7 color='#{_hex(GREY)}'>{_esc(it.rule)}</font>",
                               s["cell"]),
                     Paragraph(_esc(it.explanation) + (f"<br/><font size=7.5 color='#{_hex(GREY)}'><i>{cites}</i></font>"
                                                       if cites else ""), s["cell"])])
    sev = [SEV_COLOR[c] if (c := CONDUCT_SEV[it.status.value]) else None for it in items]
    return out + [_badge_table(rows, [24 * mm, 52 * mm, WIDTH - 76 * mm], sev)]


def _sections(result: AnalysisResult, s: dict[str, ParagraphStyle]) -> list:
    flag_sev = {f.id: f.severity.value for f in result.flags}
    out: list = []
    for i, sec in enumerate(result.report.sections, start=1):
        block: list = [Paragraph(f"{i}. {_esc(sec.title)}", s["h2"])]
        for sent in sec.sentences:
            chips = " ".join(f"<font color='#{_hex(SEV_COLOR[flag_sev[f]])}'><b>[{SEV_TXT[flag_sev[f]]}]</b></font>"
                             for f in sent.flag_ids if f in flag_sev)
            text = _esc(sent.text) + (f"  {chips}" if chips else "")
            if sent.status == "no_evidence":
                block.append(Paragraph(f"<font color='#{_hex(SEV_COLOR['amber'])}'><b>SIN EVIDENCIA · el asesor "
                                       f"debe confirmarlo.</b></font> {text}", s["missing"]))
            else:
                block.append(Paragraph(text, s["body"]))
            cites = _cites(sent.evidence) if sent.kind == "claim" else ""
            if cites:
                block.append(Paragraph(cites, s["cite"]))
            elif sent.kind == "computed" and sent.flag_ids:
                block.append(Paragraph("Calculado por el comprobador (ver banderas).", s["cite"]))
        out.append(KeepTogether(block[:3]))
        out += block[3:]
    return out


def _summary(result: AnalysisResult, s: dict[str, ParagraphStyle]) -> list:
    cs = result.client_summary
    if not cs:
        return []
    out: list = [Paragraph("Resumen para el cliente", s["h2"]), Paragraph(f"<i>{_esc(cs.title)}</i>", s["body"])]
    out += [Paragraph(f"•  {_esc(p.text)}", s["body"]) for p in cs.points]
    if cs.next_steps:
        out.append(Paragraph("<b>Próximos pasos</b>", ParagraphStyle("ns", s["body"], spaceBefore=6)))
        out += [Paragraph(f"•  {_esc(p.text)}", s["body"]) for p in cs.next_steps]
    return out


def _closing(result: AnalysisResult, s: dict[str, ParagraphStyle]) -> Table:
    r = result.report
    cover = ("No calculada: el informe está en modo plantilla." if r.template_mode else
             f"{r.coverage_pct:.0f} % de las afirmaciones sobre el cliente tienen una cita verificada en el audio.")
    t = Table([[Paragraph(f"<b>Cobertura de evidencia.</b> {cover}<br/><b>Aviso.</b> {_esc(FOOTER)}", s["note"])]],
              colWidths=[WIDTH])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), SOFT), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


def render(result: AnalysisResult) -> bytes:
    """Build the PDF bytes for `result`."""
    _register_fonts()
    s = _styles()
    story: list = [
        Paragraph("Informe de idoneidad", s["title"]),
        Paragraph("Borrador MiFID II elaborado a partir de la grabación de la reunión. "
                  "Cada afirmación sobre el cliente indica el minuto del audio en que se dijo.", s["subtitle"]),
        _meta_table(result, s), Spacer(1, 8), _kpis(result, s),
    ]
    if result.report.template_mode:
        story += [Spacer(1, 8), Paragraph(
            f"<font color='#{_hex(SEV_COLOR['amber'])}'><b>MODO PLANTILLA.</b></font> La extracción con IA falló; "
            "el asesor debe completar el informe a mano.", s["missing"])]
    story += _sections(result, s) + _flags(result, s) + _conduct(result, s)
    story.append(KeepTogether(_summary(result, s) + [Spacer(1, 14), _closing(result, s)]))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=22 * mm,
                            bottomMargin=22 * mm, title=f"Informe de idoneidad · {result.report.client_name}",
                            author="Acta", subject=f"Análisis {result.analysis_id}", creator="Acta · para GPTadvisor")
    doc.build(story, canvasmaker=_canvas_class(result))
    return buf.getvalue()
