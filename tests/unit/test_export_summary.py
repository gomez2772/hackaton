"""A-5: client summary to send to the client (copy text, PDF letter, Markdown)."""

from __future__ import annotations

import io
from pathlib import Path

import pypdf
import pytest
from streamlit.testing.v1 import AppTest

from app.export import SUMMARY_FORMATS, export_summary, first_name, human_date, summary_markdown, summary_text

APP = str(Path(__file__).resolve().parents[2] / "app" / "ui" / "streamlit_app.py")


def test_helpers():
    assert first_name("Lucía Martín (sintético)") == "Lucía"
    assert first_name("") == ""
    assert human_date("2026-11-10") == "10/11/2026"
    assert human_date("10 de noviembre") == "10 de noviembre"


def test_summary_text_is_ready_to_paste(demo_result):
    text = summary_text(demo_result)
    cs = demo_result.client_summary
    assert text.startswith("Hola, Lucía:")
    for p in cs.points + cs.next_steps:
        assert f"- {p.text}" in text
    assert "Próximos pasos:" in text
    assert demo_result.report.advisor_name in text
    assert "sintéticos" in text
    assert "[" not in text  # no timestamps or internal ids for the client


def test_summary_markdown(demo_result):
    md = summary_markdown(demo_result)
    assert md.startswith(f"# {demo_result.client_summary.title}")
    assert "## Próximos pasos" in md
    assert f"_Reunión del {human_date(demo_result.report.meeting_date)} · tu asesor:" in md
    assert md.rstrip().endswith("_Demostración con datos sintéticos._")


@pytest.mark.parametrize("fmt", list(SUMMARY_FORMATS))
def test_export_summary_all_formats(demo_result, fmt):
    data = export_summary(demo_result, fmt)
    assert len(data) > 200
    if fmt == "pdf":
        reader = pypdf.PdfReader(io.BytesIO(data))
        text = " ".join(" ".join(p.extract_text() for p in reader.pages).replace(" ", " ").split())
        assert len(reader.pages) == 1
        assert "Hola, Lucía:" in text and "Próximos pasos" in text
        assert all(" ".join(p.text.split()) in text for p in demo_result.client_summary.points)
        assert "sintéticos" in text


def test_export_summary_without_summary_raises(demo_result):
    r = demo_result.model_copy(deep=True)
    r.client_summary = None
    with pytest.raises(ValueError):
        export_summary(r, "md")


def test_ui_summary_tab_has_copy_box_and_downloads(demo_result, monkeypatch):
    monkeypatch.setenv("ACTA_FAKE_STAGES", "all")
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["result"] = demo_result
    at.session_state["audio"] = None
    at.run()
    assert not at.exception
    tab = at.tabs[4]
    assert tab.code[0].value.rstrip() == summary_text(demo_result).rstrip()
    cached = at.session_state["exports"]
    assert cached[(demo_result.analysis_id, "summary", "pdf")].startswith(b"%PDF")
    assert cached[(demo_result.analysis_id, "summary", "md")].decode().startswith("# ")
