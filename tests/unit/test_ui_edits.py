"""A-6 in the UI: edit, confirm and undo a sentence without evidence; downloads use the confirmed text."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[2] / "app" / "ui" / "streamlit_app.py")
EDITED = "La clienta indica que se jubilará en unos tres años."


@pytest.fixture
def app(demo_result, monkeypatch):
    monkeypatch.setenv("ACTA_FAKE_STAGES", "all")
    r = demo_result.model_copy(deep=True)
    s = r.report.sections[0].sentences[0]
    s.status, s.evidence = "no_evidence", []
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["result"] = r
    at.session_state["audio"] = None
    at.run()
    assert not at.exception
    return at, r, s.id


def md_export(at, r) -> str:
    return next(v for k, v in at.session_state["exports"].items() if k[0] == r.analysis_id and k[-1] == "md").decode()


def test_pending_sentence_is_editable_and_warned(app):
    at, r, sid = app
    rep = at.tabs[0]
    assert len(rep.text_area) == 1 and rep.text_area[0].value == r.report.sections[0].sentences[0].text
    assert any("pendientes de confirmar" in w.value for w in rep.warning)
    assert "[SIN EVIDENCIA: confirmar]" in md_export(at, r)


def test_confirm_edited_sentence_then_undo(app):
    at, r, sid = app
    at.tabs[0].text_area[0].set_value(EDITED).run()
    at.tabs[0].button(key=f"ok-{sid}").click().run()
    assert not at.exception
    assert at.session_state["edits"][r.analysis_id] == {sid: EDITED}
    assert not at.tabs[0].text_area and not at.tabs[0].warning
    assert any("confirmado por el asesor" in c.value for c in at.tabs[0].caption)
    md = md_export(at, r)
    assert EDITED in md and "SIN EVIDENCIA" not in md  # criterio: la frase editada sale en la exportación

    at.tabs[0].button(key=f"undo-{sid}").click().run()
    assert at.session_state["edits"][r.analysis_id] == {}
    assert len(at.tabs[0].text_area) == 1
    assert "[SIN EVIDENCIA: confirmar]" in md_export(at, r)


def test_confirm_with_empty_text_does_nothing(app):
    at, r, sid = app
    at.tabs[0].text_area[0].set_value("   ").run()
    at.tabs[0].button(key=f"ok-{sid}").click().run()
    assert not at.session_state.get("edits", {}).get(r.analysis_id)
    assert len(at.tabs[0].text_area) == 1
