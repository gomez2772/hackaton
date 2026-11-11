"""Demo clip (task C-2): the turns of fixtures/demo/transcript.json read by two ElevenLabs voices.

Run:  python scripts/make_demo_clip.py --flash          (cheap test, ~0.5 credits/char)
      python scripts/make_demo_clip.py                  (Multilingual, best quality, ~1 credit/char)
      add --check to transcribe the clip (STT, ~330 credits/min) and look for the key quote.
Output: app/data/audio/demo_clip.mp3 (or demo_clip_flash.mp3). Lines are cached, so re-running costs nothing.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import fakes  # noqa: E402
from app.audio.tts import estimate_credits, synthesize_dialogue  # noqa: E402

KEY_QUOTE = "me jubilo en tres años"
CONFIRM_ABOVE = 2000  # credits (CLAUDE.md §7: ask before expensive calls)


def main() -> None:
    """Build the demo clip and optionally verify it with a real transcription."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--flash", action="store_true", help="usa eleven_flash_v2_5 (más barato)")
    ap.add_argument("--check", action="store_true", help="transcribe el clip y busca la cita clave")
    ap.add_argument("--yes", action="store_true", help=f"confirma gastos > {CONFIRM_ABOVE} créditos")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    script = [("advisor" if s.speaker_id == "speaker_0" else "client", s.text) for s in fakes.transcript().segments]
    model = "eleven_flash_v2_5" if args.flash else "eleven_multilingual_v2"
    cost = estimate_credits(script, model)
    logging.info("%d turnos, %d caracteres, %s: ~%.0f créditos (0 si ya está en caché)",
                 len(script), sum(len(t) for _, t in script), model, cost)
    if cost > CONFIRM_ABOVE and not args.yes:
        sys.exit(f"Coste estimado {cost:.0f} > {CONFIRM_ABOVE} créditos: repite con --yes")

    name = "demo_clip_flash.mp3" if args.flash else "demo_clip.mp3"
    out = synthesize_dialogue(script, ROOT / "app" / "data" / "audio" / name, model=model)
    logging.info("listo: %s", out)

    if args.check:
        from app.audio.stt import transcribe
        from app.engine.citations import normalize

        tr = transcribe(out)
        speakers = {s.speaker_id for s in tr.segments}
        found = normalize(KEY_QUOTE) in normalize(" ".join(s.text for s in tr.segments))
        logging.info("STT: %.0f s, %d segmentos, %d hablantes, «%s» %s",
                     tr.duration_s, len(tr.segments), len(speakers), KEY_QUOTE, "OK" if found else "NO ENCONTRADA")
        if not found or len(speakers) != 2:
            sys.exit(1)


if __name__ == "__main__":
    main()
