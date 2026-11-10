"""Speech-to-text with ElevenLabs Scribe + diarization. Owner: C. Tasks C-01 (C-08 out of scope).

Contract: docs/CONTRACT.md §C·Audio.
Pending (C-1): check the endpoint, fields and response format against the current ElevenLabs
docs with a real 20 s recording (written against the public REST API, not yet run live).
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import httpx

from app.config import Settings, get_settings
from app.schemas import Segment, Transcript, Word

log = logging.getLogger(__name__)
URL = "https://api.elevenlabs.io/v1/speech-to-text"


class STTError(RuntimeError):
    """Transcription failed and no fallback was available."""


def audio_id(audio_path: Path) -> str:
    """First 16 hex chars of the sha256 of the file."""
    h = hashlib.sha256()
    with open(audio_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def transcribe(audio_path: Path, *, language: str = "es", num_speakers: int = 2,
               settings: Settings | None = None) -> Transcript:
    """Diarized transcript of `audio_path`, cached by audio_id in ACTA_CACHE_DIR/stt/."""
    s = settings or get_settings()
    aid = audio_id(audio_path)
    cache = s.cache_dir / "stt" / f"{aid}.json"
    if cache.exists():
        log.info("STT desde caché (%s): 0 créditos", aid)
        return Transcript.model_validate_json(cache.read_text(encoding="utf-8"))
    if not s.elevenlabs_api_key:
        raise STTError("Falta ELEVENLABS_API_KEY en .env")

    try:
        with open(audio_path, "rb") as f:
            r = httpx.post(URL, headers={"xi-api-key": s.elevenlabs_api_key}, timeout=300,
                           files={"file": (audio_path.name, f)},
                           data={"model_id": s.stt_model, "diarize": "true", "num_speakers": str(num_speakers),
                                 "language_code": language, "timestamps_granularity": "word"})
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise STTError(f"ElevenLabs STT falló: {e}") from e

    transcript = words_to_transcript(r.json(), aid, language)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(transcript.model_dump_json(indent=1), encoding="utf-8")
    log.info("STT %s: %d segmentos, %.0f s", aid, len(transcript.segments), transcript.duration_s)
    return transcript


def words_to_transcript(resp: dict, aid: str, language: str = "es") -> Transcript:
    """Group consecutive words of the same speaker into Segment s0000, s0001..."""
    words = [w for w in resp.get("words", []) if w.get("type", "word") == "word"]
    segments: list[Segment] = []
    current: list[dict] = []

    def flush() -> None:
        if current:
            sp = current[0].get("speaker_id") or "speaker_0"
            segments.append(Segment(
                id=f"s{len(segments):04d}", speaker_id=sp, start=float(current[0]["start"]),
                end=float(current[-1]["end"]), text=" ".join(w["text"].strip() for w in current),
                words=[Word(text=w["text"].strip(), start=float(w["start"]), end=float(w["end"]), speaker_id=sp)
                       for w in current]))
            current.clear()

    for w in words:
        if current and w.get("speaker_id") != current[-1].get("speaker_id"):
            flush()
        current.append(w)
    flush()
    return Transcript(audio_id=aid, language=language, duration_s=segments[-1].end if segments else 0.0,
                      segments=segments, stt_provider="elevenlabs")

