"""Local MiFID II knowledge base for Claude prompts (no internet, cacheable). Owner: C.

Documents in app/data/normativa/: four Spanish summaries of the official texts (each with its
source URL) and checklist_mifid.json (requirement ids IDO-xx, KYC-xx, AJU-xx, COS-xx, REG-xx).
The documents are reference material: do not edit them here, only replace them with a new version.

How the LLM calls should use it (B, app/engine/llm.py):
    system=[*system_blocks(), {"type": "text", "text": task_instructions_and_schema}]
The first block is identical in every call and carries cache_control, so extraction, conduct,
summary and report share one cached prefix (~12k tokens) and only the first call pays for it.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

DIR = Path(__file__).resolve().parent / "normativa"
CHECKLIST_FILE = "checklist_mifid.json"
ID_PATTERN = re.compile(r"\b(?:IDO|KYC|AJU|COS|REG)-\d{2}\b")

PREAMBLE = """Eres el motor de cumplimiento de Acta. Tu base normativa son los documentos de <normativa> y el checklist de <checklist>.
Reglas:
- Cuando señales un requisito, cita su id del checklist (por ejemplo IDO-08) y su fuente tal como aparece en el checklist.
- No inventes ids ni artículos que no estén en el checklist o en los documentos.
- Cada hecho sobre el cliente debe llevar una cita literal de la transcripción. Si no la hay, marca el campo como "sin evidencia".
- Los umbrales marcados como internos de Acta (p. ej. concentración del 25 %) no son límites legales: dilo así si los usas.
- No eres asesor jurídico: si un caso no está cubierto por la normativa cargada, dilo en lugar de suponer."""

# Checker flag type -> checklist requirements it implements (for the report, UI and exports)
FLAG_REQUIREMENTS: dict[str, list[str]] = {
    "sri": ["AJU-04"],
    "horizon": ["AJU-02", "IDO-03"],
    "concentration": ["AJU-01"],
    "liquidity": ["AJU-02"],
    "volatility": ["AJU-04", "AJU-06"],
}


@lru_cache(maxsize=1)
def load_documents() -> str:
    """All .md documents in name order, each wrapped in <documento nombre=...>."""
    files = sorted(p for p in DIR.glob("*.md") if p.name.lower() != "readme.md")
    if not files:
        raise FileNotFoundError(f"No hay documentos .md en {DIR}")
    parts = [f'<documento nombre="{p.name}">\n{p.read_text(encoding="utf-8").strip()}\n</documento>' for p in files]
    return "<normativa>\n" + "\n\n".join(parts) + "\n</normativa>"


@lru_cache(maxsize=1)
def load_checklist() -> tuple[dict, ...]:
    """Checklist requirements (dicts with id, bloque, requisito, fuente, ...), in file order."""
    data = json.loads((DIR / CHECKLIST_FILE).read_text(encoding="utf-8"))
    return tuple(data["requisitos"])


def requirement(req_id: str) -> dict:
    """One requirement by id; KeyError if it does not exist."""
    for r in load_checklist():
        if r["id"] == req_id:
            return r
    raise KeyError(req_id)


def requirements_by_block(block: str) -> list[dict]:
    """Requirements of one block: informe_idoneidad, conocer_cliente, ajuste_producto, costes, grabacion_registros."""
    return [r for r in load_checklist() if r["bloque"] == block]


def valid_ids() -> set[str]:
    """Every requirement id in the checklist."""
    return {r["id"] for r in load_checklist()}


def invalid_references(text: str) -> list[str]:
    """Requirement ids cited in `text` that are NOT in the checklist (likely hallucinations)."""
    ok = valid_ids()
    return sorted({i for i in ID_PATTERN.findall(text) if i not in ok})


@lru_cache(maxsize=1)
def knowledge_text() -> str:
    """Preamble + documents + checklist as one stable string (same bytes every call, so it caches)."""
    checklist = json.dumps(list(load_checklist()), ensure_ascii=False, indent=1)
    return f"{PREAMBLE}\n\n{load_documents()}\n\n<checklist>\n{checklist}\n</checklist>"


def system_blocks(task_instructions: str = "") -> list[dict]:
    """Blocks for the Messages API `system` parameter: cached regulation first, task text after."""
    blocks = [{"type": "text", "text": knowledge_text(), "cache_control": {"type": "ephemeral"}}]
    if task_instructions:
        blocks.append({"type": "text", "text": task_instructions})
    return blocks


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    text = knowledge_text()
    logging.info("%d documentos, %d requisitos, prompt de %s caracteres (~%s tokens)",
                 load_documents().count("<documento "), len(load_checklist()),
                 f"{len(text):,}".replace(",", " "), f"{len(text) // 4:,}".replace(",", " "))
