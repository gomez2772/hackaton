"""Structured extraction with literal quotes. Owner: B. Tasks B-02, B-04.

The ISIN of each recommendation is chosen by the model from the KID catalogue and then
checked by code: an ISIN outside the catalogue is dropped (never invented) and, when it is
valid, `product_name` becomes the exact KID name.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.config import Settings
from app.engine.llm import complete_json, render_transcript
from app.schemas import ClientProfile, Extraction, FundKID, Transcript

log = logging.getLogger(__name__)
PROMPT = Path(__file__).resolve().parent / "prompts" / "extraction.md"


def extract(transcript: Transcript, client: ClientProfile, *, settings: Settings | None = None,
            kids: dict[str, FundKID] | None = None) -> Extraction:
    """Circumstance changes, stated needs, recommendations and commitments, each with quotes."""
    if kids is None:
        from app.data.loaders import load_kids
        kids = load_kids()

    catalogue = [{"isin": k.isin, "name": k.name, "asset_class": k.asset_class, "sri": k.sri}
                 for k in kids.values()]
    holdings = [{"isin": h.isin, "name": h.name, "amount_eur": h.amount_eur,
                 "asset_class": kids[h.isin].asset_class if h.isin in kids else None}
                for h in client.portfolio]
    user = (
        f"PERFIL DEL CLIENTE (test de idoneidad previo):\n"
        f"{client.model_dump_json(indent=1, exclude={'portfolio'})}\n\n"
        f"CARTERA ACTUAL DEL CLIENTE (de aquí sale el dinero de compras y traspasos):\n"
        f"{json.dumps(holdings, ensure_ascii=False, indent=1)}\n\n"
        f"CATÁLOGO DE FONDOS (para el ISIN de lo recomendado):\n{json.dumps(catalogue, ensure_ascii=False)}\n\n"
        f"TRANSCRIPCIÓN (una línea por turno: [id mm:ss hablante] texto):\n{render_transcript(transcript)}"
    )
    out = complete_json(PROMPT.read_text(encoding="utf-8"), user, Extraction, effort="medium", settings=settings)
    return resolve_isins(out, kids)


def resolve_isins(extraction: Extraction, kids: dict[str, FundKID]) -> Extraction:
    """Drop ISINs not in the catalogue; use the exact KID name when the ISIN is valid."""
    recs = []
    for r in extraction.recommendations:
        isin = (r.isin or "").strip().upper() or None
        if isin and isin not in kids:
            log.warning("recomendación %s: ISIN %s fuera del catálogo; se deja sin ISIN", r.id, isin)
            recs.append(r.model_copy(update={"isin": None}))
        elif isin:
            recs.append(r.model_copy(update={"isin": isin, "product_name": kids[isin].name}))
        else:
            recs.append(r)
    return extraction.model_copy(update={"recommendations": recs})
