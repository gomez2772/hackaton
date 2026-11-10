"""Runtime settings read from environment / .env. FROZEN (see CLAUDE.md §2)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

STAGES = ("stt", "extract", "check", "conduct", "summary", "report")


def _fake_stages(raw: str) -> frozenset[str]:
    items = {s.strip().lower() for s in raw.split(",") if s.strip()}
    if "all" in items:
        return frozenset(STAGES)
    return frozenset(items & set(STAGES))


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"))
    llm_cache: bool = field(default_factory=lambda: os.getenv("ACTA_LLM_CACHE", "1") == "1")

    elevenlabs_api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    stt_model: str = field(default_factory=lambda: os.getenv("ELEVENLABS_STT_MODEL", "scribe_v2"))
    tts_model: str = field(default_factory=lambda: os.getenv("ELEVENLABS_TTS_MODEL", "eleven_flash_v2_5"))
    stt_fallback_whisper: bool = field(default_factory=lambda: os.getenv("ACTA_STT_FALLBACK", "0") == "1")

    fake_stages: frozenset[str] = field(default_factory=lambda: _fake_stages(os.getenv("ACTA_FAKE_STAGES", "")))
    cache_dir: Path = field(default_factory=lambda: ROOT / os.getenv("ACTA_CACHE_DIR", ".cache"))
    fixtures_dir: Path = ROOT / "fixtures" / "demo"
    data_dir: Path = ROOT / "app" / "data"

    api_key: str = field(default_factory=lambda: os.getenv("ACTA_API_KEY", "dev-key"))
    advisor_name: str = field(default_factory=lambda: os.getenv("ACTA_ADVISOR_NAME", "Asesor de demostración"))

    def is_fake(self, stage: str) -> bool:
        """True if `stage` must return the fixture instead of running real code."""
        return stage in self.fake_stages


def get_settings(**overrides: object) -> Settings:
    """Fresh settings; overrides are for tests (e.g. fake_stages=frozenset(STAGES))."""
    s = Settings()
    if overrides:
        from dataclasses import replace

        s = replace(s, **overrides)  # type: ignore[arg-type]
    return s
