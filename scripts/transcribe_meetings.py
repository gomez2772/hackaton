"""Transcribe the 5 evaluation meetings (C-10) and save the transcript next to each audio.

app/data/meetings/<id>/audio.mp3 -> app/data/meetings/<id>/audio.transcript.json (versioned), so
`transcribe()` and tests/eval/run_eval.py --source audio reuse it on any machine at 0 credits.
Also compares each transcript with tests/eval/meetings/<id>/script.json (turns, speakers, words).

Run:  python scripts/transcribe_meetings.py            (shows the cost and stops if > 2 000 credits)
      python scripts/transcribe_meetings.py --yes
"""

from __future__ import annotations

import argparse
import difflib
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.audio.stt import audio_id, sidecar, transcribe  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.engine.citations import normalize  # noqa: E402
from app.schemas import Transcript  # noqa: E402

AUDIO = ROOT / "app" / "data" / "meetings"
SCRIPTS = ROOT / "tests" / "eval" / "meetings"
CREDITS_PER_MIN = 330
CONFIRM_ABOVE = 2000
BYTES_PER_MIN = 128_000 / 8 * 60  # mp3_44100_128


def compare(tr: Transcript, turns: list[list[str]]) -> dict:
    """Turn count, speaker agreement (best speaker->role mapping) and word similarity vs the script."""
    roles = [who for who, _ in turns]
    first = tr.segments[0].speaker_id if tr.segments else ""
    pred = ["advisor" if s.speaker_id == first else "client" for s in tr.segments]
    n = min(len(pred), len(roles))
    speakers = sum(p == r for p, r in zip(pred, roles, strict=False)) / max(len(roles), 1)
    said = normalize(" ".join(s.text for s in tr.segments)).split()
    script = normalize(" ".join(t for _, t in turns)).split()
    words = difflib.SequenceMatcher(a=script, b=said, autojunk=False).ratio()
    return {"turns_script": len(roles), "turns_stt": len(tr.segments), "aligned": n,
            "speaker_agreement": round(speakers, 3), "word_similarity": round(words, 3)}


def main() -> None:
    """Estimate, transcribe, save sidecars and print the comparison."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help=f"confirma gastos > {CONFIRM_ABOVE} créditos")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    audios = sorted(AUDIO.glob("*/audio.mp3"))
    s = get_settings()
    pending = [a for a in audios if not (s.cache_dir / "stt" / f"{audio_id(a)}.json").exists() and not sidecar(a).exists()]
    cost = sum(a.stat().st_size / BYTES_PER_MIN * CREDITS_PER_MIN for a in pending)
    logging.info("%d reuniones, %d sin transcribir: ~%.0f créditos", len(audios), len(pending), cost)
    if cost > CONFIRM_ABOVE and not args.yes:
        sys.exit(f"Coste estimado {cost:.0f} > {CONFIRM_ABOVE} créditos: repite con --yes")

    for a in audios:
        tr = transcribe(a, settings=s)
        sidecar(a).write_text(tr.model_dump_json(indent=1), encoding="utf-8")
        turns = json.loads((SCRIPTS / a.parent.name / "script.json").read_text(encoding="utf-8"))["turns"]
        logging.info("%s: %.0f s · %s", a.parent.name, tr.duration_s, compare(tr, turns))


if __name__ == "__main__":
    main()
