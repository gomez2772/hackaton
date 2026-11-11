"""A-6: the advisor edits/confirms sentences without evidence; the edited sentence goes to every export."""

from __future__ import annotations

import io
import json

import pypdf
import pytest

from app.export import CONFIRMED_LABEL, apply_edits, export, is_confirmed, sentence_text

EDITED = "La clienta indica que se jubilará en unos tres años."


@pytest.fixture
def unsupported(demo_result):
    """Demo result whose first sentence (p1) has no evidence."""
    r = demo_result.model_copy(deep=True)
    s = r.report.sections[0].sentences[0]
    s.status, s.evidence = "no_evidence", []
    return r


def first(r):
    return r.report.sections[0].sentences[0]


def test_apply_edits_marks_confirmed_without_inventing_evidence(unsupported):
    out = apply_edits(unsupported, {first(unsupported).id: f"  {EDITED} "})
    s = first(out)
    assert is_confirmed(s) and sentence_text(s) == EDITED
    assert s.status == "no_evidence" and s.evidence == []  # CLAUDE.md §9: still no quote in the audio
    assert out.report.coverage_pct == unsupported.report.coverage_pct
    assert first(unsupported).text != s.text  # the original result is not modified


def test_apply_edits_never_touches_sentences_with_evidence(demo_result):
    s = first(demo_result)
    out = apply_edits(demo_result, {s.id: "Texto inventado"})
    assert first(out).text == s.text and not is_confirmed(first(out))


def test_apply_edits_ignores_empty_text(unsupported):
    out = apply_edits(unsupported, {first(unsupported).id: "   "})
    assert not is_confirmed(first(out))


@pytest.mark.parametrize("fmt", ["md", "html", "docx", "pdf"])
def test_edited_sentence_goes_to_the_export(unsupported, fmt):
    data = export(apply_edits(unsupported, {first(unsupported).id: EDITED}), fmt)
    if fmt == "pdf":
        text = "\n".join(p.extract_text() for p in pypdf.PdfReader(io.BytesIO(data)).pages)
    elif fmt == "docx":
        from docx import Document

        text = "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    else:
        text = data.decode()
    text = " ".join(text.replace(" ", " ").split())
    assert EDITED in text
    assert CONFIRMED_LABEL in text.lower()
    # report-sentence markers only («SIN EVIDENCIA» also exists as a conduct status in the PDF table)
    assert "SIN EVIDENCIA: confirmar" not in text and "SIN EVIDENCIA · el asesor" not in text
    assert "⟦" not in text  # the internal marker never reaches people


def test_unconfirmed_sentence_still_flagged(unsupported):
    assert "[SIN EVIDENCIA: confirmar]" in export(unsupported, "md").decode()


def test_json_keeps_the_machine_readable_marker(unsupported):
    data = json.loads(export(apply_edits(unsupported, {first(unsupported).id: EDITED}), "json"))
    s = data["report"]["sections"][0]["sentences"][0]
    assert s["status"] == "no_evidence" and s["text"].startswith(EDITED) and "confirmado por el asesor" in s["text"]
