"""Live ElevenLabs Scribe check (C-1). Spends ~330 credits/min the first time; cached afterwards.

Run: ACTA_STT_SAMPLE=path/to/20s_two_speakers.m4a pytest -m live tests/unit/test_stt_live.py
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.audio.stt import transcribe

SAMPLE = os.getenv("ACTA_STT_SAMPLE", "")


@pytest.mark.live
@pytest.mark.skipif(not SAMPLE, reason="define ACTA_STT_SAMPLE con un audio de dos hablantes")
def test_real_transcript_has_two_speakers():
    tr = transcribe(Path(SAMPLE))
    assert tr.segments and tr.stt_provider == "elevenlabs"
    assert len({s.speaker_id for s in tr.segments}) == 2
    assert transcribe(Path(SAMPLE)) == tr  # second call served from cache
