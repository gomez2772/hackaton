"""Stage progress board and audio saving for the Streamlit UI (A-2). Owner: A.

Pure helpers (no Streamlit) so they can be unit-tested. The pipeline calls `on_stage(name)` when a
stage STARTS; a stage ends when the next one starts or when the whole analysis returns.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from pathlib import Path

STAGE_ORDER: tuple[str, ...] = ("stt", "extract", "validate", "check", "conduct", "summary", "report")


def secs(x: float) -> str:
    """1.25 -> '1,3 s' (Spanish decimal comma)."""
    return f"{x:.1f} s".replace(".", ",")


class StageProgress:
    """Tracks which pipeline stage is running and how long each finished one took."""

    def __init__(self, clock: Callable[[], float] = time.perf_counter) -> None:
        self._clock = clock
        self.done: list[tuple[str, float]] = []
        self.current: str | None = None
        self.failed: str | None = None
        self._t0 = 0.0

    def start(self, stage: str) -> None:
        """Called by the pipeline's on_stage: closes the running stage and opens `stage`."""
        self._close()
        self.current, self._t0 = stage, self._clock()

    def finish(self) -> None:
        """The analysis returned: the running stage is done."""
        self._close()

    def fail(self) -> None:
        """The analysis raised while `current` was running."""
        self.failed, self.current = self.current, None

    @property
    def fraction(self) -> float:
        """Share of the 7 stages already finished (0-1)."""
        return min(len(self.done) / len(STAGE_ORDER), 1.0)

    def markdown(self, labels: dict[str, str]) -> str:
        """One line per stage: ✅ done (with time), ⏳ running, ❌ failed, ◻️ pending."""
        took = dict(self.done)
        lines = []
        for st in STAGE_ORDER:
            label = labels.get(st, st)
            if st in took:
                lines.append(f"✅ {label} · {secs(took[st])}")
            elif st == self.current:
                lines.append(f"⏳ **{label}…**")
            elif st == self.failed:
                lines.append(f"❌ **{label}**: ha fallado")
            else:
                lines.append(f"◻️ :gray[{label}]")
        return "  \n".join(lines)

    def _close(self) -> None:
        if self.current is not None:
            self.done.append((self.current, self._clock() - self._t0))
            self.current = None


def save_audio(data: bytes, name: str, folder: Path) -> Path:
    """Save an uploaded or recorded audio under a content-hash name (no overwrites, no duplicates)."""
    folder.mkdir(parents=True, exist_ok=True)
    p = Path(name)
    path = folder / f"{p.stem}-{hashlib.sha256(data).hexdigest()[:12]}{p.suffix.lower() or '.wav'}"
    if not path.exists():
        path.write_bytes(data)
    return path
