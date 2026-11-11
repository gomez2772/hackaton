"""A-8: automated rehearsal of the 2-minute demo script (docs/DEMO.md §2) in plan-B mode (ACTA_FAKE_STAGES=all).

Each test is one beat of the script and checks that the screen shows what the presenter says. If the
fixture or the script changes (e.g. other figures), this fails on purpose: update DEMO.md and this test together.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app import fakes

APP = str(Path(__file__).resolve().parents[2] / "app" / "ui" / "streamlit_app.py")


@pytest.fixture
def demo(monkeypatch):
    monkeypatch.setenv("ACTA_FAKE_STAGES", "all")
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["demo"] = "1"
    at.run()
    assert not at.exception
    return at


@pytest.fixture
def analysed(demo):
    demo.button(key="run-main").click().run()
    assert not demo.exception
    return demo


def test_0_00_portada(demo):
    """«Lucía, perfil moderado, 100 000 € invertidos.»"""
    assert any("Lucía Martín" in m.value and "perfil de riesgo 3 de 5" in m.value and "cartera 100 000 €" in m.value
               for m in demo.markdown)
    assert demo.button(key="run-main").label == "▶ Analizar la reunión de demostración"


def test_0_15_se_ven_las_7_etapas(analysed):
    """«Se ven pasar las 7 etapas»: in demo mode the board stays open, without simulated times."""
    status = analysed.get("status")
    assert status and status[0].label == "Análisis completado"
    board = next(m.value for m in analysed.markdown if m.value.startswith("✅"))
    assert board.count("✅") == 7


def test_0_30_banderas_rojas(analysed):
    """«La volatilidad … 12,8 %, por encima del 12 % de su perfil. Y el fondo pide 5 años, pero ella se jubila en 3.»"""
    assert next(m.value for m in analysed.metric if m.label == "Idoneidad") == "No idóneo"
    assert next(m.value for m in analysed.metric if m.label == "Alertas rojas") == "2"
    reds = [m.value for m in analysed.tabs[1].markdown if m.value.startswith("🔴")]
    assert len(reds) == 2
    assert any("Horizonte" in r and "5 años > 3 años" in r for r in reds)
    assert any("Volatilidad" in r and "12,8 % > 12,0 %" in r for r in reds)


def test_0_55_play_horizonte_suena_la_cita(analysed):
    """«Pulsar el ▶ de la bandera de horizonte» → se oye «me jubilo en tres años» sin tocar el reproductor."""
    if fakes.demo_audio() is None:
        pytest.skip("sin clip de la demo (C-2)")
    play = analysed.tabs[1].button[0]
    assert play.help == "«me jubilo en tres años»"
    play.click().run()
    audio = analysed.get("audio")[0].proto
    assert audio.autoplay and audio.url.endswith(".mp3")
    turn = next(s for s in fakes.transcript().segments if "me jubilo en tres años" in s.text)
    assert audio.start_time == int(turn.start) and audio.end_time == int(turn.end) + 1
    analysed.run()  # any later rerun must not start playing again by itself
    assert not analysed.get("audio")[0].proto.autoplay


def test_1_10_conducta(analysed):
    """«Promesa de rentabilidad … y nadie le explicó los riesgos.»"""
    breaches = [m.value for m in analysed.tabs[2].markdown if "No cumple" in m.value]
    assert len(breaches) == 2
    assert any("promesas de rentabilidad" in b for b in breaches) and any("Riesgos explicados" in b for b in breaches)
    assert next(m.value for m in analysed.metric if m.label == "Incumplimientos de conducta") == "2"


def test_1_30_informe_y_pdf(analysed):
    """«Pestaña Informe de idoneidad → botón PDF».

    AppTest has no accessor for download buttons, so the check is on the cached export they serve."""
    rid = analysed.session_state["result"].analysis_id
    assert analysed.session_state["exports"][(rid, "report", "pdf")].startswith(b"%PDF")


def test_1_45_resumen_para_el_cliente(analysed):
    """«Un resumen en lenguaje llano para enviárselo a Lucía.»"""
    assert analysed.tabs[4].code[0].value.startswith("Hola, Lucía:")
