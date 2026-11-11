"""A-2: record in the browser, per-stage progress with timings, clean errors."""

from __future__ import annotations

import io
import wave
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app.pipeline import analyze
from app.ui.progress import STAGE_ORDER, StageProgress, save_audio, secs

APP = str(Path(__file__).resolve().parents[2] / "app" / "ui" / "streamlit_app.py")


def wav_10s() -> bytes:
    """10 s of silence, 16 kHz mono: what st.audio_input hands over."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 16000 * 10)
    return buf.getvalue()


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def test_secs_uses_decimal_comma():
    assert secs(1.26) == "1,3 s"
    assert secs(0) == "0,0 s"


def test_stage_progress_times_each_stage():
    clock = Clock()
    p = StageProgress(clock)
    p.start("stt")
    clock.t = 2.0
    p.start("extract")
    clock.t = 5.5
    assert p.done == [("stt", 2.0)]
    assert p.current == "extract"
    md = p.markdown({"stt": "Transcribiendo", "extract": "Extrayendo"})
    assert "✅ Transcribiendo · 2,0 s" in md and "⏳ **Extrayendo…**" in md and "◻️" in md
    p.finish()
    assert p.done[-1] == ("extract", 3.5) and p.current is None
    assert p.fraction == pytest.approx(2 / 7)


def test_stage_progress_marks_failed_stage():
    p = StageProgress(Clock())
    p.start("stt")
    p.fail()
    assert p.failed == "stt"
    assert "❌ **stt**: ha fallado" in p.markdown({})


def test_save_audio_is_content_addressed(tmp_path):
    a = save_audio(b"uno", "grabacion.wav", tmp_path)
    assert save_audio(b"uno", "grabacion.wav", tmp_path) == a
    assert save_audio(b"dos", "grabacion.wav", tmp_path) != a
    assert save_audio(b"x", "Reunión.MP3", tmp_path).suffix == ".mp3"
    assert a.read_bytes() == b"uno"


def test_recording_of_10s_goes_through_the_7_stages(tmp_path, demo_client, fake_settings):
    """Criterio de A-2: grabar 10 s y ver pasar las 7 etapas."""
    path = save_audio(wav_10s(), "grabacion.wav", tmp_path)
    p = StageProgress()
    seen: list[str] = []

    def on_stage(stage: str) -> None:
        seen.append(stage)
        p.start(stage)

    result = analyze(path, demo_client, settings=fake_settings, on_stage=on_stage)
    p.finish()
    assert seen == list(STAGE_ORDER)
    assert [t.stage for t in result.timings] == list(STAGE_ORDER)
    assert p.fraction == 1.0 and p.markdown({}).count("✅") == 7


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("ACTA_FAKE_STAGES", "all")
    return AppTest.from_file(APP, default_timeout=60)


def test_ui_shows_seven_finished_stages_and_total(app):
    app.run()
    app.sidebar.button[0].click().run()
    assert not app.exception
    board = next(m.value for m in app.markdown if m.value.startswith("✅"))
    assert board.count("✅") == 7
    assert any(c.value.startswith("⏱ Total") for c in app.caption)


def test_analyze_disabled_until_there_is_a_recording(app):
    app.run()
    app.sidebar.radio[0].set_value("Grabar ahora").run()
    assert app.sidebar.button[0].disabled
    assert any("Graba o sube" in c.value for c in app.sidebar.caption)


def test_stt_failure_shows_error_not_traceback(app, monkeypatch):
    from app import pipeline
    from app.audio.stt import STTError

    def boom(*args, on_stage=None, **kwargs):
        on_stage("stt")
        raise STTError("Falta ELEVENLABS_API_KEY en .env")

    monkeypatch.setattr(pipeline, "analyze", boom)
    app.run()
    app.sidebar.button[0].click().run()
    assert not app.exception
    assert any("ELEVENLABS_API_KEY" in e.value for e in app.error)
    assert any("❌" in m.value for m in app.markdown)
    assert "result" not in app.session_state
