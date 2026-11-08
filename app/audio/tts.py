"""Two-voice meeting synthesis for test data (ElevenLabs TTS). Owner: C. Tasks C-06, C-07.

Budget: eleven_flash_v2_5 costs ~0.5 credits/character. Keep meetings to 3-5 minutes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

Line = tuple[Literal["advisor", "client"], str]


def synthesize_dialogue(script: list[Line], out_path: Path) -> Path:
    """Render each line with the advisor/client voice and concatenate into one audio file.

    TODO(C-06): voices from ELEVENLABS_VOICE_ADVISOR / ELEVENLABS_VOICE_CLIENT, short pause
    between turns, cache each line by hash(text, voice, model) so re-runs cost nothing.
    """
    raise NotImplementedError("C-06: synthesize_dialogue() pendiente.")
