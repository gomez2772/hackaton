"""A-7: demo mode (?demo=1) — preloaded client and clip, brand, no empty screens, reset between rehearsals."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[2] / "app" / "ui" / "streamlit_app.py")


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("ACTA_FAKE_STAGES", "all")
    return AppTest.from_file(APP, default_timeout=60)


def demo(app: AppTest) -> AppTest:
    app.query_params["demo"] = "1"
    app.run()
    assert not app.exception
    return app


def test_demo_landing_is_never_empty(app):
    at = demo(app)
    md = [m.value for m in at.markdown]
    assert "#### Verbatim" in md
    assert any("en minutos" in m for m in md)
    assert any("Lucía Martín" in m and "perfil de riesgo 3 de 5" in m for m in md)
    assert at.button(key="run-main").label == "▶ Analizar la reunión de demostración"
    assert not at.sidebar.info  # no «Etapas simuladas» in demo mode


def test_demo_preloads_demo_client_and_clip(app):
    at = demo(app)
    assert at.sidebar.toggle[0].value is True
    assert at.sidebar.selectbox[0].value.client_id == "CLI-DEMO-001"
    assert at.sidebar.radio[0].value == "Clip de la demo"


def test_demo_run_from_main_button_then_reset(app, monkeypatch):
    from app import fakes

    monkeypatch.setattr(fakes, "demo_audio", lambda: None)  # independent of whether C-2's clip is in the repo
    at = demo(app)
    at.button(key="run-main").click().run()
    assert not app.exception and "result" in at.session_state
    assert not any(m.value.startswith("## De la reunión") for m in at.markdown)  # landing gone
    assert not any(c.value.startswith("⏱ Total") for c in at.caption)  # no simulated 0,0 s timings
    assert any("Audio no disponible en esta demostración" in c.value for c in at.caption)
    at.button(key="reset").click().run()
    assert "result" not in at.session_state
    assert any("en minutos" in m.value for m in at.markdown)


def test_demo_plays_the_clip_when_it_exists(app, monkeypatch, tmp_path):
    from app import fakes

    clip = tmp_path / "demo_clip.mp3"
    clip.write_bytes(b"ID3" + b"\x00" * 64)
    monkeypatch.setattr(fakes, "demo_audio", lambda: clip)
    at = demo(app)
    at.button(key="run-main").click().run()
    assert not at.exception
    assert at.session_state["audio"] == clip
    assert len(at.main.get("audio")) == 1
    assert not any("Audio no disponible" in c.value for c in at.caption)


def test_toggle_keeps_url_in_sync(app):
    at = demo(app)
    at.sidebar.toggle[0].set_value(False).run()
    assert "demo" not in at.query_params
    assert any("Etapas simuladas" in i.value for i in at.sidebar.info)
    at.sidebar.toggle[0].set_value(True).run()
    assert at.query_params["demo"] == ["1"] or at.query_params["demo"] == "1"


def test_normal_mode_landing_also_not_empty(app):
    app.run()
    assert not app.exception
    assert app.sidebar.toggle[0].value is False
    assert any("en minutos" in m.value for m in app.markdown)
    assert any("barra lateral" in c.value for c in app.caption)
