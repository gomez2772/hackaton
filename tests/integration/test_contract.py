"""Contract tests: fixtures obey the schemas and the fake pipeline runs end to end. Owner: D."""

from __future__ import annotations

from app.engine.citations import coverage
from app.export import FORMATS, export
from app.pipeline import analyze
from app.schemas import AnalysisResult, Severity


def test_fixtures_are_consistent(demo_transcript, demo_extraction, demo_flags):
    seg_ids = {s.id for s in demo_transcript.segments}
    texts = {s.id: s.text for s in demo_transcript.segments}
    all_ev = [e for group in (demo_extraction.circumstance_changes, demo_extraction.stated_needs,
                              demo_extraction.recommendations, demo_extraction.commitments)
              for item in group for e in item.evidence]
    assert all_ev, "la extracción demo debe tener evidencias"
    for e in all_ev:
        assert e.segment_id in seg_ids
        assert e.quote in texts[e.segment_id], f"cita no literal: {e.quote!r}"
    rec_ids = {r.id for r in demo_extraction.recommendations}
    assert all(f.recommendation_id in rec_ids for f in demo_flags)


def test_demo_flags_match_story(demo_flags):
    by_type = {f.type.value: f.severity for f in demo_flags}
    assert by_type["horizon"] == Severity.RED
    assert by_type["volatility"] == Severity.RED
    assert by_type["concentration"] == Severity.AMBER


def test_fake_pipeline_end_to_end(fake_settings, demo_client):
    stages_seen: list[str] = []
    result = analyze(None, demo_client, settings=fake_settings, on_stage=stages_seen.append)
    core = ["stt", "extract", "validate", "check", "report"]
    assert [st for st in stages_seen if st in core] == core
    assert set(stages_seen) <= {*core, "conduct", "summary"}
    assert result.analysis_id.startswith("AN-")
    assert all(t.fake for t in result.timings)


def test_result_json_roundtrip(demo_result):
    again = AnalysisResult.model_validate_json(demo_result.model_dump_json())
    assert again == demo_result


def test_coverage_of_demo_report(demo_result):
    assert coverage(demo_result.report) == 100.0 == demo_result.report.coverage_pct


def test_json_export_and_formats(demo_result):
    assert set(FORMATS) == {"pdf", "docx", "md", "html", "json"}
    assert export(demo_result, "json").startswith(b"{")


def test_conduct_and_summary_fixtures_quote_the_transcript(demo_transcript):
    from app import fakes

    texts = {s.id: s.text for s in demo_transcript.segments}
    evs = [e for it in fakes.conduct().items for e in it.evidence]
    summary = fakes.client_summary()
    evs += [e for p in summary.points + summary.next_steps for e in p.evidence]
    assert evs
    for e in evs:
        assert e.quote in texts[e.segment_id], f"cita no literal: {e.quote!r}"
    codes = {it.code: it.status.value for it in fakes.conduct().items}
    assert codes["return_promise"] == "breach"
