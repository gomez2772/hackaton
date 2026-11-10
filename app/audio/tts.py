"""Two-voice meeting synthesis for test data (ElevenLabs TTS). Owner: C. Tasks C-2, C-7.

Budget: eleven_flash_v2_5 costs ~0.5 credits/character. Keep meetings to 3-4 minutes.
Each line is cached by hash(text, voice, model), so re-runs cost nothing.
Pending (C-2): try it live; set ELEVENLABS_VOICE_ADVISOR / ELEVENLABS_VOICE_CLIENT in .env.
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
                        settings: Settings | None = None) -> Path:
    """Render each line with the advisor/client voice and concatenate into one mp3."""
    s = settings or get_settings()
    voices = {"advisor": os.getenv("ELEVENLABS_VOICE_ADVISOR", ""), "client": os.getenv("ELEVENLABS_VOICE_CLIENT", "")}
    if not all(voices.values()):
        raise RuntimeError("Define ELEVENLABS_VOICE_ADVISOR y ELEVENLABS_VOICE_CLIENT en .env")
    model = model or s.tts_model
    chunks = [_line(text, voices[who], model, s) for who, text in script]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(b"".join(chunks))  # MP3 frames concatenate cleanly
    log.info("audio de %d turnos en %s", len(script), out_path)
    return out_path


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
