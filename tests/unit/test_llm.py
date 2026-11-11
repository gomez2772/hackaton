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


class RecordingClient:
    """Fake client that records kwargs; first answer is cut at max_tokens (only thinking)."""

    def __init__(self, answers: list[tuple[str, str]]):
        self.answers, self.calls, self.messages = answers, [], self

    def create(self, **kw):
        stop, text = self.answers[min(len(self.calls), len(self.answers) - 1)]
        self.calls.append(kw)
        content = [SimpleNamespace(type="thinking", thinking="")]
        if text:
            content.append(SimpleNamespace(type="text", text=text))
        return SimpleNamespace(content=content, stop_reason=stop, model="fake",
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5))


def test_truncated_by_max_tokens_is_retried_with_more_room_not_fed_back(tmp_path):
    fake = RecordingClient([("max_tokens", ""), ("end_turn", '{"title": "Resumen de tu reunión"}')])
    out = complete_json("sys", "user", ClientSummary, max_tokens=2000, effort="low",
                        settings=_settings(tmp_path), client=fake)
    assert out.title == "Resumen de tu reunión"
    assert [c["max_tokens"] for c in fake.calls] == [2000, 21000]
    assert all(c["output_config"] == {"effort": "low"} for c in fake.calls)
    assert len(fake.calls[1]["messages"]) == 1  # the truncated answer is not sent back


def test_effort_is_part_of_the_cache_key(tmp_path):
    a = RecordingClient([("end_turn", '{"title": "A"}')])
    b = RecordingClient([("end_turn", '{"title": "B"}')])
    s = _settings(tmp_path)
    assert complete_json("sys", "u", ClientSummary, effort="low", settings=s, client=a).title == "A"
    assert complete_json("sys", "u", ClientSummary, effort="high", settings=s, client=b).title == "B"


def test_knowledge_sends_cached_regulation_block_first(tmp_path):
    fake = RecordingClient([("end_turn", '{"title": "T"}')])
    complete_json("sys", "u", ClientSummary, knowledge=True, settings=_settings(tmp_path), client=fake)
    system = fake.calls[0]["system"]
    assert isinstance(system, list) and system[0]["cache_control"] == {"type": "ephemeral"}
    assert "<checklist>" in system[0]["text"] and system[-1]["text"].startswith("sys")
    plain = RecordingClient([("end_turn", '{"title": "P"}')])
    out = complete_json("sys", "u", ClientSummary, settings=_settings(tmp_path), client=plain)
    assert out.title == "P" and isinstance(plain.calls[0]["system"], str)  # different cache key
