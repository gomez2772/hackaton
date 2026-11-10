"""Claude client with strict JSON output. Owner: B. Task B-01.

Every LLM call of the engine goes through `complete_json`, so cost and caching are
controlled in one place: responses are cached on disk by hash (ACTA_LLM_CACHE=1) and token
usage is appended to ACTA_CACHE_DIR/llm/usage.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import Settings, get_settings

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """The model did not return valid JSON for the schema after retries."""


def complete_json(system: str, user: str, schema: type[T], *, max_tokens: int = 8000,
                  settings: Settings | None = None, client: Any = None) -> T:
    """Call Claude (settings.anthropic_model) and return a validated `schema` instance."""
    s = settings or get_settings()
    full_system = (
        f"{system}\n\nResponde SOLO con un objeto JSON válido que cumpla este JSON Schema, "
        f"sin texto antes ni después:\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
    )
    key = hashlib.sha256(f"{s.anthropic_model}\n{full_system}\n{user}".encode()).hexdigest()[:24]
    cache_file = s.cache_dir / "llm" / f"{key}.json"
    if s.llm_cache and cache_file.exists():
        try:
            return schema.model_validate_json(cache_file.read_text(encoding="utf-8"))
        except ValidationError:
            log.warning("caché LLM inválida para %s; se vuelve a llamar", key)

    if client is None:
        if not s.anthropic_api_key:
            raise LLMError("Falta ANTHROPIC_API_KEY en .env")
        import anthropic

        client = anthropic.Anthropic(api_key=s.anthropic_api_key)

    messages: list[dict[str, str]] = [{"role": "user", "content": user}]
    last_error: Exception | None = None
    for attempt in range(3):  # first try + 2 retries feeding back the error
        try:
            resp = client.messages.create(model=s.anthropic_model, max_tokens=max_tokens,
                                          system=full_system, messages=messages)
        except Exception as e:  # network / API errors
            raise LLMError(f"Error llamando a Claude: {e}") from e
        _log_usage(s, resp)
        text = "".join(getattr(b, "text", "") for b in resp.content)
        try:
            out = schema.model_validate_json(_json_block(text))
        except (ValidationError, ValueError) as e:
            last_error = e
            log.warning("JSON no válido (intento %d): %s", attempt + 1, str(e)[:200])
            messages += [{"role": "assistant", "content": text},
                         {"role": "user", "content": f"El JSON no es válido: {e}. Devuélvelo corregido, solo JSON."}]
            continue
        if s.llm_cache:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(out.model_dump_json(indent=1), encoding="utf-8")
        return out
    raise LLMError(f"Claude no devolvió JSON válido tras 3 intentos: {last_error}")


def _json_block(text: str) -> str:
    """Outermost {...} of the response (tolerates ```json fences)."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("la respuesta no contiene JSON")
    return m.group(0)


def _log_usage(s: Settings, resp: Any) -> None:
    usage = getattr(resp, "usage", None)
    if usage is None:
        return
    rec = {"t": round(time.time()), "model": getattr(resp, "model", s.anthropic_model),
           "in": getattr(usage, "input_tokens", 0), "out": getattr(usage, "output_tokens", 0)}
    log.info("tokens: %d entrada · %d salida", rec["in"], rec["out"])
    path = s.cache_dir / "llm" / "usage.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def render_transcript(transcript: Any) -> str:
    """One line per segment: '[s0007 01:04 speaker_1] text' (what the model sees)."""
    lines = []
    for seg in transcript.segments:
        mm, ss = divmod(int(seg.start), 60)
        lines.append(f"[{seg.id} {mm:02d}:{ss:02d} {seg.speaker_id}] {seg.text}")
    return "\n".join(lines)
