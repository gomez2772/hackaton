"""A-4: professional PDF. Checks the CONTRACT §A·Exportación content list on the real PDF text."""

from __future__ import annotations

import io

import pypdf
import pytest

from app.export import FOOTER, export, mmss, verdict
from app.export.pdf import _esc


def pdf_text(data: bytes) -> tuple[str, pypdf.PdfReader]:
    reader = pypdf.PdfReader(io.BytesIO(data))
    text = "\n".join(p.extract_text() for p in reader.pages).replace(" ", " ")
    return " ".join(text.split()), reader


@pytest.fixture
def degraded(demo_result):
    r = demo_result.model_copy(deep=True)
    r.report.template_mode = True
    r.conduct = None
    r.client_summary = None
    s = r.report.sections[0].sentences[0]
    s.status, s.evidence = "no_evidence", []
    return r


def test_pdf_contains_everything_the_contract_lists(demo_result):
    text, reader = pdf_text(export(demo_result, "pdf"))
    r = demo_result.report
    # header: client, advisor, date, analysis id
    for v in (r.client_name, r.advisor_name, r.meeting_date, demo_result.analysis_id):
        assert v in text
    # the 6 sections
    for sec in r.sections:
        assert sec.title in text
    # flags with their computation
    for f in demo_result.flags:
        assert f.title in text and " ".join(f.explanation.split()) in text
    # coverage and citations with [mm:ss]
    assert "Cobertura de evidencia" in text and "100 %" in text
    ev = r.sections[0].sentences[0].evidence[0]  # time taken from the fixture: survives regenerating it (A-8)
    assert f"[{mmss(ev.start)}] «{ev.quote}»" in text
    # conduct and client summary
    assert "NO CUMPLE" in text and "Resumen para el cliente" in text
    # disclaimer: synthetic data and AI draft
    assert " ".join(FOOTER.split()) in text
    # page footer and metadata
    n = len(reader.pages)
    assert f"Página 1 de {n}" in text and f"Página {n} de {n}" in text
    assert reader.metadata.title.startswith("Informe de idoneidad")


def test_pdf_keeps_unicode_symbols(demo_result):
    text, _ = pdf_text(export(demo_result, "pdf"))
    assert "≤" in text and "€" in text and "<=" not in text


def test_pdf_degraded_result(degraded):
    text, _ = pdf_text(export(degraded, "pdf"))
    assert "MODO PLANTILLA" in text
    assert "SIN EVIDENCIA" in text
    assert "El chequeo de conducta no está disponible" in text
    assert "Resumen para el cliente" not in text


def test_pdf_without_flags(demo_result):
    r = demo_result.model_copy(deep=True)
    r.flags = []
    text, _ = pdf_text(export(r, "pdf"))
    assert "Sin evaluar" in text and "No se han generado banderas" in text


@pytest.mark.parametrize(("sevs", "expected"), [
    ([], "Sin evaluar"), (["green"], "Idóneo"), (["green", "amber"], "Con advertencias"),
    (["amber", "red"], "No idóneo"),
])
def test_verdict(demo_result, sevs, expected):
    r = demo_result.model_copy(deep=True)
    r.flags = [f.model_copy(update={"severity": type(f.severity)(s)}) for f, s in zip(r.flags, sevs, strict=False)]
    assert verdict(r) == expected


def test_numbers_do_not_wrap():
    assert _esc("70 000 € y 16,0 %") == "70 000 € y 16,0 %"
    assert _esc("a < b & c") == "a &lt; b &amp; c"
