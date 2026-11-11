"""Citation validator (B-03)."""

from __future__ import annotations

import pytest

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


# --- Numbers: digits and Spanish words are equivalent (C's request) -------------------------

def _wtr(*texts: str) -> Transcript:
    """One segment per text, one Word per space-separated chunk, 1 s per word."""
    segs, t = [], 0.0
    for k, text in enumerate(texts):
        words = [Word(text=w, start=t + i, end=t + i + 0.5, speaker_id="speaker_0")
                 for i, w in enumerate(text.split())]
        segs.append(Segment(id=f"s{k:04d}", speaker_id="speaker_0", start=t, end=t + len(words),
                            text=text, words=words))
        t += len(words)
    return Transcript(audio_id="n", duration_s=t, stt_provider="fixture", segments=segs)


@pytest.mark.parametrize(("said", "quoted"), [
    ("quiero invertir treinta mil euros", "quiero invertir 30 000 euros"),
    ("quiero invertir treinta mil euros", "quiero invertir 30.000 euros"),
    ("quiero invertir treinta mil euros", "quiero invertir 30000 euros"),
    ("quiero invertir 30.000 euros", "quiero invertir treinta mil euros"),
    ("quiero invertir 30 000 euros", "quiero invertir 30.000 euros"),
    ("me jubilo en veinte años", "me jubilo en 20 años"),
    ("me jubilo en 3 años", "me jubilo en tres años"),
    ("gastos de cero coma veinticinco por ciento al año", "gastos de 0,25 % al año"),
    ("gastos de 0,2 % al año", "gastos de cero coma dos por ciento al año"),
    ("puede caer un 30 % o más", "puede caer un treinta por ciento o más"),
    ("puede caer un 30% o más", "puede caer un 30 % o más"),
    ("tiene ciento veinte mil en renta fija", "tiene 120.000 en renta fija"),
    ("un millón doscientos mil euros", "1.200.000 euros"),
    ("treinta y cinco mil euros", "35.000 euros"),
    ("son novecientos noventa y nueve mil novecientos noventa y nueve euros", "son 999 999 euros"),
    ("dentro de dos mil veinticinco", "dentro de 2025"),
    ("nada menos que 1,5 millones", "nada menos que un millón quinientos mil"),
])
def test_number_forms_are_equivalent(said, quoted):
    assert locate(quoted, _wtr(said)).verified


@pytest.mark.parametrize(("said", "quoted"), [
    ("quiero invertir 20 000 euros", "quiero invertir treinta mil euros"),
    ("quiero invertir veinte mil euros", "quiero invertir 30.000 euros"),
    ("gastos de 0,2 % al año", "gastos de cero coma veinticinco por ciento al año"),
    ("puede caer un 30 % o más", "puede caer un cuarenta por ciento o más"),
    ("ciento veinte mil en renta fija", "20.000 en renta fija"),
    ("me jubilo en 3 años", "me jubilo en trece años"),
])
def test_different_number_is_not_verified(said, quoted):
    assert not locate(quoted, _wtr(said)).verified


def test_collapsed_number_keeps_first_start_and_last_end():
    tr = _wtr("hola", "propongo invertir veinte mil euros en un fondo")  # words at 1..8 s
    ev = locate("invertir 20.000", tr)
    assert ev.verified and ev.segment_id == "s0001" and (ev.start, ev.end) == (2, 4.5)


def test_percent_words_map_to_digit_and_sign_times():
    tr = _wtr("puede caer un 30 % en un mal año")  # «30» at 3 s, «%» at 4 s
    ev = locate("caer un treinta por ciento", tr)
    assert ev.verified and (ev.start, ev.end) == (1, 4.5)
    ev = locate("puede caer un 30 % en un mal año", _wtr("puede caer un treinta por ciento en un mal año"))
    assert ev.verified and (ev.start, ev.end) == (0, 9.5)


def test_number_across_two_segments():
    ev = locate("veinte mil. Vale, 30 %", _wtr("necesito veinte mil", "Vale, treinta por ciento"))
    assert ev.verified and ev.segment_id == "s0000" and (ev.start, ev.end) == (1, 6.5)


def test_partial_number_quotes_still_match_as_before():
    tr = _wtr("tiene ochenta mil euros en un fondo")
    assert locate("mil euros en un fondo", tr).verified  # cuts «ochenta mil»: plain fallback
    assert locate("un fondo", tr).verified
    assert not locate("1 fondo", tr).verified  # «un» as an article is not the number 1


def test_normalize_is_unchanged_for_numbers():
    assert normalize("Un 30 %, o 0,2 € y 30.000") == "un 30 o 0 2 y 30 000"
