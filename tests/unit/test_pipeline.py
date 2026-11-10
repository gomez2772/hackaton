"""Pipeline orchestration (B-04): 7 stages and graceful degradation without API keys."""

from __future__ import annotations

from app.config import STAGES, get_settings
from app.pipeline import analyze


def test_fake_pipeline_runs_seven_stages(demo_client):
    seen: list[str] = []
    res = analyze(None, demo_client, settings=get_settings(fake_stages=frozenset(STAGES)), on_stage=seen.append)
    assert seen == ["stt", "extract", "validate", "check", "conduct", "summary", "report"]
    assert res.conduct and res.client_summary and not res.warnings


def test_degrades_without_api_key(demo_client, tmp_path):
    s = get_settings(fake_stages=frozenset({"stt", "check"}), anthropic_api_key="", llm_cache=False, cache_dir=tmp_path)
    res = analyze(None, demo_client, settings=s)
    assert res.report.template_mode
    assert res.conduct is None and res.client_summary is None
    assert len(res.warnings) == 3
    assert all(seg.role.value != "unknown" for seg in res.transcript.segments)
