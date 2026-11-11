"""STT word grouping (C-01) without calling the API."""

from __future__ import annotations

from app.audio.stt import words_to_transcript


def test_words_grouped_by_speaker():
    resp = {"words": [
        {"text": "Hola", "start": 0.0, "end": 0.4, "type": "word", "speaker_id": "speaker_0"},
        {"text": " ", "start": 0.4, "end": 0.5, "type": "spacing", "speaker_id": "speaker_0"},
        {"text": "Lucía.", "start": 0.5, "end": 1.0, "type": "word", "speaker_id": "speaker_0"},
        {"text": "Hola.", "start": 1.2, "end": 1.6, "type": "word", "speaker_id": "speaker_1"},
    ]}
    tr = words_to_transcript(resp, "abc")
    assert [s.id for s in tr.segments] == ["s0000", "s0001"]
    assert tr.segments[0].text == "Hola Lucía." and tr.segments[1].speaker_id == "speaker_1"
    assert tr.duration_s == 1.6 and tr.stt_provider == "elevenlabs"


def test_sidecar_transcript_used_only_if_audio_matches(tmp_path, monkeypatch):
    from dataclasses import replace

    import app.audio.stt as stt
    from app.config import get_settings

    audio = tmp_path / "clip.mp3"
    audio.write_bytes(b"audio bytes")
    s = replace(get_settings(), cache_dir=tmp_path / "cache", elevenlabs_api_key="")
    tr = words_to_transcript({"words": [{"text": "Hola", "start": 0, "end": 1, "speaker_id": "speaker_0"}]},
                             stt.audio_id(audio))
    stt.sidecar(audio).write_text(tr.model_dump_json(), encoding="utf-8")
    monkeypatch.setattr(stt.httpx, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("API llamada")))
    assert stt.sidecar(audio).name == "clip.transcript.json"
    assert stt.transcribe(audio, settings=s) == tr

    audio.write_bytes(b"otro audio")  # sidecar no longer matches: falls through to the API (no key -> STTError)
    try:
        stt.transcribe(audio, settings=s)
        raise AssertionError("debía fallar")
    except stt.STTError:
        pass


def test_null_timestamps_and_audio_events_skipped():
    resp = {"audio_duration_secs": 3.0, "words": [
        {"text": "(risas)", "start": 0.0, "end": 0.3, "type": "audio_event", "speaker_id": "speaker_0"},
        {"text": "Bien.", "start": None, "end": None, "type": "word", "speaker_id": "speaker_0"},
        {"text": "Vale.", "start": 1.0, "end": 1.4, "type": "word", "speaker_id": "speaker_1"},
    ]}
    tr = words_to_transcript(resp, "abc")
    assert [s.text for s in tr.segments] == ["Vale."]
    assert tr.duration_s == 3.0


def test_cache_hit_does_not_call_api(tmp_path, monkeypatch):
    from dataclasses import replace

    import app.audio.stt as stt
    from app.config import get_settings

    audio = tmp_path / "a.mp3"
    audio.write_bytes(b"fake audio")
    s = replace(get_settings(), cache_dir=tmp_path, elevenlabs_api_key="")
    tr = words_to_transcript({"words": [{"text": "Hola", "start": 0, "end": 1, "speaker_id": "speaker_0"}]},
                             stt.audio_id(audio))
    (tmp_path / "stt").mkdir()
    (tmp_path / "stt" / f"{tr.audio_id}.json").write_text(tr.model_dump_json(), encoding="utf-8")
    monkeypatch.setattr(stt.httpx, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("API llamada")))
    assert stt.transcribe(audio, settings=s) == tr
