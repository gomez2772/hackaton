"""Template report (B-05)."""

from __future__ import annotations

from app.engine.report import draft


def test_report_from_fixture_has_full_coverage(demo_extraction, demo_flags, demo_client, demo_transcript):
    rep = draft(demo_extraction, demo_flags, demo_client, demo_transcript, advisor_name="A", meeting_date="2026-11-10")
    assert [s.key for s in rep.sections] == ["client_situation", "objectives_and_needs", "recommendations",
                                             "suitability_assessment", "risks_and_warnings", "commitments"]
    assert rep.coverage_pct == 100.0
    text = " ".join(s.text for sec in rep.sections for s in sec.sentences)
    assert "NO es idónea" in text and "30 000 €" in text
    computed = [s for sec in rep.sections for s in sec.sentences if s.kind == "computed"]
    assert computed and all(s.flag_ids for s in computed)
