"""Audio of the synthetic evaluation meetings (task C-7) with ElevenLabs TTS (Flash).

Reads tests/eval/meetings/<id>/script.json ({"turns": [[who, text], ...]}) and writes
app/data/meetings/<id>/audio.mp3. Lines are cached, so re-running costs nothing.

Run:  python scripts/make_meeting_audio.py              (shows the cost and stops if > 2 000 credits)
      python scripts/make_meeting_audio.py --yes        (generates every meeting)
      python scripts/make_meeting_audio.py m01_horizonte_sri --yes
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.audio.tts import estimate_credits, synthesize_dialogue  # noqa: E402

MEETINGS = ROOT / "tests" / "eval" / "meetings"
OUT = ROOT / "app" / "data" / "meetings"
MODEL = "eleven_flash_v2_5"
CONFIRM_ABOVE = 2000  # credits (CLAUDE.md §7)


def load_script(meeting_dir: Path) -> list[tuple[str, str]]:
    """Turns of one meeting as (advisor|client, text) tuples."""
    data = json.loads((meeting_dir / "script.json").read_text(encoding="utf-8"))
    turns = [(who, text) for who, text in data["turns"]]
    bad = {who for who, _ in turns} - {"advisor", "client"}
    if bad:
        raise ValueError(f"{meeting_dir.name}: hablantes desconocidos {bad}")
    return turns


def main() -> None:
    """Estimate the cost and synthesize the requested meetings."""
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="por defecto, todas las reuniones de tests/eval/meetings")
    ap.add_argument("--yes", action="store_true", help=f"confirma gastos > {CONFIRM_ABOVE} créditos")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    dirs = [MEETINGS / i for i in args.ids] if args.ids else sorted(p.parent for p in MEETINGS.glob("*/script.json"))
    scripts = {d.name: load_script(d) for d in dirs}
    total = 0.0
    for name, turns in scripts.items():
        cost = estimate_credits(turns, MODEL)
        total += cost
        logging.info("%s: %d turnos, ~%.0f créditos", name, len(turns), cost)
    logging.info("total ~%.0f créditos (0 lo que ya esté en caché)", total)
    if total > CONFIRM_ABOVE and not args.yes:
        sys.exit(f"Coste estimado {total:.0f} > {CONFIRM_ABOVE} créditos: repite con --yes")

    for name, turns in scripts.items():
        out = synthesize_dialogue(turns, OUT / name / "audio.mp3", model=MODEL)
        logging.info("listo: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
