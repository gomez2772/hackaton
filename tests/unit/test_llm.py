"""LLM client (B-01) with a fake Anthropic client: invalid JSON -> retry -> valid."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.config import get_settings
from app.engine.llm import LLMError, complete_json
from app.schemas import ClientSummary


class FakeClient:
    def __init__(self, answers: list[str]):
        self.answers = answers
        self.calls = 0
        self.messages = self

    def create(self, **_):
        text = self.answers[min(self.calls, len(self.answers) - 1)]
        self.calls += 1
        return SimpleNamespace(content=[SimpleNamespace(text=text)], model="fake",
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5))


def _settings(tmp_path):
    return get_settings(anthropic_api_key="x", llm_cache=True, cache_dir=tmp_path)


def test_retry_then_valid_and_cached(tmp_path):
    fake = FakeClient(["esto no es json", '```json\n{"title": "Resumen de tu reunión"}\n```'])
    out = complete_json("sys", "user", ClientSummary, settings=_settings(tmp_path), client=fake)
    assert out.title == "Resumen de tu reunión" and fake.calls == 2
    again = complete_json("sys", "user", ClientSummary, settings=_settings(tmp_path), client=FakeClient(["x"]))
    assert again == out  # served from disk cache


def test_gives_up_after_three_attempts(tmp_path):
    fake = FakeClient(["nada"])
    with pytest.raises(LLMError):
        complete_json("sys", "u2", ClientSummary, settings=_settings(tmp_path), client=fake)
    assert fake.calls == 3
