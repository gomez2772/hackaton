"""Demo clip (task C-2): the turns of fixtures/demo/transcript.json read by two ElevenLabs voices.

Run:  python scripts/make_demo_clip.py            (Multilingual voice, best quality, ~2 500 credits)
      python scripts/make_demo_clip.py --flash    (cheaper, for tests)
Output: app/data/audio/demo_clip.mp3. Lines are cached, so re-running costs nothing.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import fakes  # noqa: E402
from app.audio.tts import synthesize_dialogue  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--flash", action="store_true", help="usa eleven_flash_v2_5 (más barato)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    script = [("advisor" if s.speaker_id == "speaker_0" else "client", s.text) for s in fakes.transcript().segments]
    chars = sum(len(t) for _, t in script)
    logging.info("%d turnos, %d caracteres", len(script), chars)
    out = synthesize_dialogue(script, ROOT / "app" / "data" / "audio" / "demo_clip.mp3",
                              model="eleven_flash_v2_5" if args.flash else "eleven_multilingual_v2")
    logging.info("listo: %s", out)


if __name__ == "__main__":
    main()
