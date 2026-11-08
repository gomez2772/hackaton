"""Claude client with strict JSON output. Owner: B. Task B-01."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """The model did not return valid JSON for the schema after retries."""


def complete_json(system: str, user: str, schema: type[T], *, max_tokens: int = 8000) -> T:
    """Call Claude (settings.anthropic_model) and return a validated `schema` instance.

    TODO(B-01): anthropic.Anthropic().messages.create(...) with the JSON schema in the system
    prompt (schema.model_json_schema()), parse, validate, retry twice feeding back the
    ValidationError, disk cache keyed by sha256(model+system+user) when settings.llm_cache,
    log input/output tokens.
    """
    raise NotImplementedError("B-01: complete_json() pendiente.")
