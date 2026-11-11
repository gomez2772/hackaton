"""A-8: UI with C's real clients and catalogue, the «Redactar el informe con IA» toggle (B-6), and no false «Idóneo»."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app.config import get_settings
from app.data.loaders import list_clients
from app.export import INCOMPLETE, export, unchecked_note, unchecked_recommendations, verdict
from app.pipeline import analyze

APP = str(Path(__file__).resolve().parents[2] / "app" / "ui" / "streamlit_app.py")
NO_API = frozenset({"stt", "extract", "conduct", "summary"})  # checker and template report run for real, no API cost


def render(result) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["result"] = result
    at.session_state["audio"] = None
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


@pytest.mark.parametrize("client", list_clients(), ids=lambda c: c.client_id)
def test_every_real_client_renders_and_exports(client):
    r = analyze(None, client, settings=get_settings(fake_stages=NO_API))
    assert r.report.client_name == client.name
    for fmt in ("pdf", "docx", "md", "html", "json"):
        assert export(r, fmt)
    render(r)


def test_unchecked_recommendation_is_never_idoneo(demo_result):
    """The fixture's ISIN is not in C's real KID catalogue: the checker skips SRI/horizon/concentration."""
    r = demo_result.model_copy(deep=True)
    r.flags = [f for f in r.flags if f.type.value in ("liquidity", "volatility")]
    for f in r.flags:
        f.severity = type(f.severity)("green")
    assert [x.id for x in unchecked_recommendations(r)] == ["r1"]
    assert verdict(r) == INCOMPLETE
    assert r.extraction.recommendations[0].product_name in unchecked_note(r)
    at = render(r)
    assert next(m.value for m in at.metric if m.label == "Idoneidad") == INCOMPLETE
    assert any("No se ha podido comprobar" in w.value for w in at.warning)
    md = export(r, "md").decode()
    assert f"Idoneidad: {INCOMPLETE}" in md and "ATENCIÓN: No se ha podido comprobar" in md


def test_red_flag_still_wins_over_incomplete(demo_result):
    r = demo_result.model_copy(deep=True)
    r.flags = [f for f in r.flags if f.type.value != "sri"]  # r1 unchecked for SRI, but there are red flags
    assert verdict(r) == "No idóneo"


def test_fixture_is_fully_checked(demo_result):
    assert unchecked_recommendations(demo_result) == [] and unchecked_note(demo_result) == ""


@pytest.fixture
def app(monkeypatch):
    return AppTest.from_file(APP, default_timeout=60), monkeypatch


def ia_toggle(at: AppTest):
    return next(t for t in at.sidebar.toggle if t.label == "Redactar el informe con IA")


def test_ia_toggle_off_by_default_and_disabled_when_report_is_simulated(app):
    at, mp = app
    mp.setenv("ACTA_FAKE_STAGES", "all")
    at.run()
    assert ia_toggle(at).value is False and ia_toggle(at).disabled


def test_ia_toggle_passes_polish_report_and_shows_model(app, demo_result):
    at, mp = app
    mp.setenv("ACTA_FAKE_STAGES", "stt,extract,check,conduct,summary")
    from app import pipeline

    seen = {}

    def fake_analyze(*args, polish_report=False, on_stage=None, **kwargs):
        seen["polish_report"] = polish_report
        r = demo_result.model_copy(deep=True)
        r.report.model = "plantilla+claude-sonnet-5-5" if polish_report else "plantilla"
        return r

    mp.setattr(pipeline, "analyze", fake_analyze)
    at.run()
    assert not ia_toggle(at).disabled
    at.sidebar.button[0].click().run()
    assert seen == {"polish_report": False}
    assert any(c.value == "✍️ Redacción: plantilla" for c in at.tabs[0].caption)
    ia_toggle(at).set_value(True).run()
    at.sidebar.button[0].click().run()
    assert seen == {"polish_report": True}
    assert any("plantilla mejorada por IA (claude-sonnet-5-5)" in c.value for c in at.tabs[0].caption)


def test_ia_requested_but_unavailable_says_so(app, demo_result):
    at, mp = app
    mp.setenv("ACTA_FAKE_STAGES", "stt,extract,check,conduct,summary")
    from app import pipeline

    def fake_analyze(*args, polish_report=False, on_stage=None, **kwargs):
        r = demo_result.model_copy(deep=True)
        r.report.model = "plantilla"  # Claude failed: B-6 silently keeps the template
        return r

    mp.setattr(pipeline, "analyze", fake_analyze)
    at.run()
    ia_toggle(at).set_value(True).run()
    at.sidebar.button[0].click().run()
    assert any("no estuvo disponible" in c.value for c in at.tabs[0].caption)


def test_demo_landing_shows_lucia_real_portfolio(app):
    at, mp = app
    mp.setenv("ACTA_FAKE_STAGES", "all")
    at.query_params["demo"] = "1"
    at.run()
    lucia = next(c for c in list_clients() if c.client_id == "CLI-DEMO-001")
    total = sum(h.amount_eur for h in lucia.portfolio)
    assert any(f"cartera {total:,.0f} €".replace(",", " ") in m.value for m in at.markdown)
    assert any(all(h.name in c.value for h in lucia.portfolio) for c in at.caption)
