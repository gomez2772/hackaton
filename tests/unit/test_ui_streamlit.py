"""Streamlit UI (A-1): renders the demo result and degraded results without errors or misleading values."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[2] / "app" / "ui" / "streamlit_app.py")


@pytest.fixture(autouse=True)
def _all_fake(monkeypatch):
    monkeypatch.setenv("ACTA_FAKE_STAGES", "all")


def render(result) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["result"] = result
    at.session_state["audio"] = None
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def metric(at: AppTest, label: str) -> str:
    return next(m.value for m in at.metric if m.label == label)


def test_analyze_button_runs_full_demo():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    at.sidebar.button[0].click().run()
    assert not at.exception
    assert metric(at, "Idoneidad") == "No idóneo"
    assert [t.label for t in at.tabs] == ["Informe de idoneidad", "Banderas", "Conducta",
                                         "Transcripción", "Resumen para el cliente"]


def test_stage_timings_in_spanish(demo_result):
    at = render(demo_result)
    timings = next(c.value for c in at.caption if "(sim.)" in c.value)
    assert "Transcripción" in timings and "stt" not in timings
    assert "0,0 s" in timings


def test_missing_conduct_is_not_shown_as_zero_breaches(demo_result):
    r = demo_result.model_copy(deep=True)
    r.conduct = None
    r.client_summary = None
    assert metric(render(r), "Incumplimientos de conducta") == "—"


def test_no_flags_shows_message(demo_result):
    r = demo_result.model_copy(deep=True)
    r.flags = []
    at = render(r)
    assert metric(at, "Idoneidad") == "Sin evaluar"
    assert any("no ha generado banderas" in i.value for i in at.tabs[1].info)


def test_unknown_speakers_get_readable_names(demo_result):
    r = demo_result.model_copy(deep=True)
    for seg in r.transcript.segments:
        seg.role = type(seg.role)("unknown")
    lines = [m.value for m in render(r).tabs[3].markdown]
    assert lines[0].startswith("🗣️ Hablante 1:")
    assert not any("speaker_" in x for x in lines)


def test_jump_button_moves_player_and_reuses_exports(demo_result):
    at = render(demo_result)
    cached = dict(at.session_state["exports"])
    assert {fmt for _, kind, fmt in cached if kind == "report"} == {"pdf", "docx", "md", "html", "json"}
    assert {fmt for _, kind, fmt in cached if kind == "summary"} == {"pdf", "md"}
    at.tabs[1].button[0].click().run()
    assert at.session_state["t"] > 0
    assert at.session_state["exports"] == cached
