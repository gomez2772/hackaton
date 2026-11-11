"""A-3: cited fragments of the transcript highlighted by type, with a legend."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from app.schemas import Evidence
from app.ui.highlight import Cite, by_segment, find_span, legend, render_segment, segment_spans

APP = str(Path(__file__).resolve().parents[2] / "app" / "ui" / "streamlit_app.py")


def cite(kind: str, quote: str) -> Cite:
    return Cite(kind, "x1", Evidence(quote=quote, segment_id="s0", verified=True))


def test_find_span_tolerates_case_accents_and_punctuation():
    text = "Eso es. Me jubilo en TRES años, ¿vale?"
    s, e = find_span(text, "me jubilo en tres anos")
    assert text[s:e] == "Me jubilo en TRES años"
    assert find_span("¿Hay algún gasto?", "hay algun gasto") == (1, 16)
    assert find_span("nada que ver", "me jubilo") is None
    assert find_span("jubilo", "") is None


def test_find_span_matches_whole_words_only():
    assert find_span("los tresillos", "tres") is None


def test_overlap_goes_to_higher_priority_kind():
    text = "me jubilo en tres años"
    runs = segment_spans(text, [cite("need", text), cite("circumstance", text)])
    assert runs == [(0, len(text), "circumstance")]
    md = render_segment(text, [cite("need", text), cite("circumstance", text)])
    assert ":blue-background[me jubilo en tres años]" in md
    assert ":blue-badge[Circunstancia]" in md and ":green-badge[Necesidad]" in md  # both types listed


def test_quote_not_found_paints_whole_segment():
    text = "y el resto de la frase"
    assert segment_spans(text, [cite("commitment", "texto que empieza en el segmento anterior")]) == [
        (0, len(text), "commitment")]


def test_markdown_special_chars_are_escaped():
    md = render_segment("Coste *bajo* [1] $5", [])
    assert md == r"Coste \*bajo\* \[1\] \$5"


def test_fixture_highlights_every_type(demo_result):
    segs = {s.id: s.text for s in demo_result.transcript.segments}
    cited = by_segment(demo_result)
    s3 = render_segment(segs["s0003"], cited["s0003"])
    assert ":blue-background[me jubilo en tres años]" in s3
    s8 = render_segment(segs["s0008"], cited["s0008"])
    assert ":red-background[con este no va a perder dinero]" in s8
    assert ":violet-background[vendiendo parte de la renta fija]" in s8
    key = legend(demo_result)
    for label in ("Circunstancia · 1", "Necesidad · 3", "Recomendación · 2", "Compromiso · 1",
                  "Conducta: incumplimiento · 3", "Conducta: correcta · 3"):
        assert label in key


def test_unverified_quotes_are_not_highlighted(demo_result):
    r = demo_result.model_copy(deep=True)
    for item in r.extraction.recommendations:
        for e in item.evidence:
            e.verified = False
    assert "Recomendación" not in legend(r)


def test_ui_transcript_tab_shows_legend_and_highlights(demo_result, monkeypatch):
    monkeypatch.setenv("ACTA_FAKE_STAGES", "all")
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["result"] = demo_result
    at.session_state["audio"] = None
    at.run()
    assert not at.exception
    md = [m.value for m in at.tabs[3].markdown]
    assert md[0].startswith("**Citas usadas en el análisis:**") and "Compromiso · 1" in md[0]
    assert any(":orange-background[Le enviaré por correo" in m for m in md)
