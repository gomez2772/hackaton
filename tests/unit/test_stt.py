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
