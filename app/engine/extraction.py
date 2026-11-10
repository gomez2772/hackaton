"""Structured extraction with literal quotes. Owner: B. Tasks B-02, B-06, B-07."""

from __future__ import annotations

from app.schemas import ClientProfile, Extraction, Transcript


def extract(transcript: Transcript, client: ClientProfile) -> Extraction:
    """Circumstance changes, stated needs, recommendations and commitments, each with quotes.

    TODO(B-02): render the transcript as "[s0007 00:24 speaker_1] text" lines, load
    prompts/extraction.md, call llm.complete_json(..., Extraction). Evidence.quote must be a
    short literal substring; segment_id/start/end are filled later by citations.validate().
    """
    raise NotImplementedError("B-02: extract() pendiente. Usa ACTA_FAKE_STAGES=extract mientras tanto.")
