"""Two-voice meeting synthesis for test data (ElevenLabs TTS). Owner: C. Tasks C-2, C-7.

Budget: eleven_flash_v2_5 costs ~0.5 credits/character. Keep meetings to 3-4 minutes.
Each line is cached by hash(text, voice, model), so re-runs cost nothing.
Turns are joined with short silent MP3 frames (no ffmpeg needed) so diarization sees the turn change.
Voices in .env: ELEVENLABS_VOICE_ADVISOR / ELEVENLABS_VOICE_CLIENT (Spanish, Spain: see DECISIONS.md).
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Literal

import httpx

from app.config import Settings, get_settings

log = logging.getLogger(__name__)
Line = tuple[Literal["advisor", "client"], str]
URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"


def synthesize_dialogue(script: list[Line], out_path: Path, *, model: str | None = None,
                        pause_s: float = 0.5, settings: Settings | None = None) -> Path:
    """Render each line with the advisor/client voice and concatenate into one mp3 with pauses."""
    s = settings or get_settings()
    voices = {"advisor": os.getenv("ELEVENLABS_VOICE_ADVISOR", ""), "client": os.getenv("ELEVENLABS_VOICE_CLIENT", "")}
    if not all(voices.values()):
        raise RuntimeError("Define ELEVENLABS_VOICE_ADVISOR y ELEVENLABS_VOICE_CLIENT en .env")
    model = model or s.tts_model
    chunks = [_line(text, voices[who], model, s) for who, text in script]
    gap = silence_like(chunks[0], pause_s) if chunks else b""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(gap.join(chunks))  # MP3 frames concatenate cleanly
    log.info("audio de %d turnos en %s", len(script), out_path)
    return out_path


def estimate_credits(script: list[Line], model: str) -> float:
    """Approximate TTS credits: ~0.5/char for Flash/Turbo, ~1/char otherwise."""
    per_char = 0.5 if ("flash" in model or "turbo" in model) else 1.0
    return per_char * sum(len(t) for _, t in script)


_BITRATES = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]  # MPEG-1 Layer III, kbps
_RATES = [44100, 48000, 32000]


def silence_like(mp3: bytes, seconds: float) -> bytes:
    """Silent MPEG-1 Layer III frames with the same header as `mp3` (empty if the format is not recognised)."""
    i = 0
    if mp3[:3] == b"ID3" and len(mp3) >= 10:  # skip ID3v2 tag (syncsafe size)
        i = 10 + ((mp3[6] & 0x7F) << 21 | (mp3[7] & 0x7F) << 14 | (mp3[8] & 0x7F) << 7 | (mp3[9] & 0x7F))
    while i + 4 <= len(mp3) and not (mp3[i] == 0xFF and (mp3[i + 1] & 0xFE) == 0xFA):
        i += 1  # sync word + MPEG-1 + Layer III
    if i + 4 > len(mp3):
        return b""
    b1, b2, b3 = mp3[i + 1] | 0x01, mp3[i + 2] & 0xFD, mp3[i + 3]  # no CRC, no padding
    br_idx, sr_idx = b2 >> 4, (b2 >> 2) & 0x03
    if not 0 < br_idx < 15 or sr_idx > 2:
        return b""
    size = 144 * _BITRATES[br_idx] * 1000 // _RATES[sr_idx]
    frame = bytes([0xFF, b1, b2, b3]) + bytes(size - 4)  # zeroed side info decodes as silence
    return frame * max(1, round(seconds * _RATES[sr_idx] / 1152))


def _line(text: str, voice: str, model: str, s: Settings) -> bytes:
    key = hashlib.sha256(f"{voice}|{model}|{text}".encode()).hexdigest()[:24]
    cache = s.cache_dir / "tts" / f"{key}.mp3"
    if cache.exists():
        return cache.read_bytes()
    r = httpx.post(URL.format(voice=voice), headers={"xi-api-key": s.elevenlabs_api_key}, timeout=120,
                   json={"text": text, "model_id": model})
    r.raise_for_status()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(r.content)
    log.info("TTS: %d caracteres", len(text))
    return r.content
