"""Structured extraction with literal quotes. Owner: B. Tasks B-02, B-04.

Pending (B-1/B-4): tune prompts/extraction.md on the demo clip and the synthetic meetings.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.engine.llm import complete_json, render_transcript
from app.schemas import ClientProfile, Extraction, Transcript

PROMPT = Path(__file__).resolve().parent / "prompts" / "extraction.md"


def extract(transcript: Transcript, client: ClientProfile, *, settings: Settings | None = None) -> Extraction:
    """Circumstance changes, stated needs, recommendations and commitments, each with quotes."""
    from app.data.loaders import load_kids

    catalogue = [{"isin": k.isin, "name": k.name, "asset_class": k.asset_class} for k in load_kids().values()]
    user = (
        f"PERFIL DEL CLIENTE (test de idoneidad previo):\n{client.model_dump_json(indent=1)}\n\n"
        f"CATÁLOGO DE FONDOS (para el ISIN):\n{json.dumps(catalogue, ensure_ascii=False)}\n\n"
        f"TRANSCRIPCIÓN (una línea por turno: [id mm:ss hablante] texto):\n{render_transcript(transcript)}"
    )
    return complete_json(PROMPT.read_text(encoding="utf-8"), user, Extraction, settings=settings)
