"""Speech-to-text with ElevenLabs Scribe + diarization. Owner: C. Tasks C-01, C-08.

Contract: docs/CONTRACT.md §C·Audio.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from app.schemas import Transcript

log = logging.getLogger(__name__)


class STTError(RuntimeError):
    """Transcription failed and no fallback was available."""


def audio_id(audio_path: Path) -> str:
    """First 16 hex chars of the sha256 of the file."""
    h = hashlib.sha256()
    with open(audio_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def transcribe(audio_path: Path, *, language: str = "es", num_speakers: int = 2) -> Transcript:
    """Diarized transcript of `audio_path`, cached by audio_id in ACTA_CACHE_DIR/stt/.

    TODO(C-01):
      1. If cache_dir/stt/<audio_id>.json exists -> return it (no credits spent).
      2. ElevenLabs(api_key).speech_to_text.convert(file=..., model_id=settings.stt_model,
         diarize=True, num_speakers=num_speakers, language_code=language,
         timestamps_granularity="word").
      3. Group consecutive words of the same speaker_id into Segment(id=f"s{i:04d}", ...).
      4. Save to cache and return Transcript(stt_provider="elevenlabs").
    TODO(C-08): on failure and settings.stt_fallback_whisper -> faster-whisper locally.
    """
    raise NotImplementedError("C-01: transcribe() pendiente. Usa ACTA_FAKE_STAGES=stt mientras tanto.")
