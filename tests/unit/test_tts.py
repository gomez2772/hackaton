"""TTS helpers (C-2) without calling the API."""

from __future__ import annotations

from dataclasses import replace

import pytest

import app.audio.tts as tts
from app.config import get_settings

# MPEG-1 Layer III, 128 kbps, 44.1 kHz, mono, no CRC: frames of 417 bytes
HEADER = bytes([0xFF, 0xFB, 0x90, 0xC4])


def test_silence_matches_header_and_length():
    mp3 = b"ID3" + bytes([4, 0, 0, 0, 0, 0, 2]) + b"\x00\x00" + HEADER + bytes(413)
    sil = tts.silence_like(mp3, 0.5)
    assert len(sil) % 417 == 0 and len(sil) // 417 == 19  # 0.5 s * 44100 / 1152
    assert sil[:4] == HEADER and not any(sil[4:417])


def test_silence_unknown_format_is_empty():
    assert tts.silence_like(b"not an mp3", 0.5) == b""


def test_estimate_credits():
    script = [("advisor", "a" * 100), ("client", "b" * 100)]
    assert tts.estimate_credits(script, "eleven_flash_v2_5") == 100
    assert tts.estimate_credits(script, "eleven_multilingual_v2") == 200


def test_dialogue_uses_cache_and_inserts_pauses(tmp_path, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_VOICE_ADVISOR", "va")
    monkeypatch.setenv("ELEVENLABS_VOICE_CLIENT", "vc")
    s = replace(get_settings(), cache_dir=tmp_path)
    chunk = HEADER + bytes(413)
    calls = []

    def fake_line(text, voice, model, settings):
        calls.append(voice)
        return chunk

    monkeypatch.setattr(tts, "_line", fake_line)
    out = tts.synthesize_dialogue([("advisor", "Hola"), ("client", "Hola")], tmp_path / "x.mp3",
                                  model="eleven_flash_v2_5", pause_s=0.5, settings=s)
    assert calls == ["va", "vc"]
    assert out.stat().st_size == 2 * 417 + 19 * 417


def test_missing_voices_raise(tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_VOICE_ADVISOR", raising=False)
    with pytest.raises(RuntimeError):
        tts.synthesize_dialogue([("advisor", "x")], tmp_path / "x.mp3")
