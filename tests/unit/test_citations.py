"""Citation validator (B-03)."""

from __future__ import annotations

from app.engine.citations import locate, normalize, validate
from app.schemas import Segment, Transcript, Word


def _tr() -> Transcript:
    words = [Word(text=w, start=20 + i, end=20.9 + i, speaker_id="speaker_1")
             for i, w in enumerate("Pues sí. Me jubilo en tres años.".split())]
    return Transcript(audio_id="t", duration_s=40, stt_provider="fixture", segments=[
        Segment(id="s0000", speaker_id="speaker_1", start=20, end=27, text="Pues sí. Me jubilo en tres años.", words=words),
        Segment(id="s0001", speaker_id="speaker_0", start=27, end=31, text="Entendido, tres años."),
    ])


def test_normalize_accents_case_punctuation():
    assert normalize("  ¿Años?  MÁS, sí ") == "anos mas si"


def test_exact_quote_gets_word_time():
    ev = locate("me jubilo en tres años", _tr())
    assert ev.verified and ev.segment_id == "s0000" and ev.start == 22 and ev.end == 26.9


def test_accent_and_case_tolerance():
    assert locate("ME JUBILO EN TRES ANOS", _tr()).verified


def test_missing_quote_is_not_verified():
    ev = locate("me jubilo en cuatro años", _tr())
    assert not ev.verified and ev.segment_id is None


def test_quote_across_two_segments():
    ev = locate("tres años. Entendido", _tr())
    assert ev.verified and ev.segment_id == "s0000"


def test_validate_relocates_fixture_evidence(demo_extraction, demo_transcript):
    out = validate(demo_extraction, demo_transcript)
    evs = [e for r in out.recommendations for e in r.evidence]
    assert evs and all(e.verified for e in evs)
