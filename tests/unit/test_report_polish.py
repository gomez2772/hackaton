"""Optional Claude rewrite of the report (B-6) with a fake LLM: only safe rewrites are kept."""

from __future__ import annotations

import pytest

from app.engine import report as report_mod
from app.engine.llm import LLMError
from app.engine.report import _Rewrite, _Rewrites, draft, safe_rewrite


@pytest.mark.parametrize(("orig", "new", "ok"), [
    ("La recomendación NO es idónea: horizonte.", "La recomendación no es idónea por el horizonte.", True),
    ("El asesor recomienda invertir 30 000 € en X.", "Se recomienda invertir 30 000 € en X.", True),
    ("El asesor recomienda invertir 30 000 € en X.", "Se recomienda invertir 25 000 € en X.", False),
    ("Necesita liquidez (aprox. 20 000 €).", "Necesita liquidez.", False),
    ("No se mencionan costes.", "Se mencionan costes.", False),
    ("Concentración: 30 % > 25 %.", "La recomendación es idónea: 30 % > 25 %.", False),
    ("Texto.", "", False),
])
def test_safe_rewrite(orig, new, ok):
    assert safe_rewrite(orig, new) is ok


def _base(demo_extraction, demo_flags, demo_client, demo_transcript, **kw):
    return draft(demo_extraction, demo_flags, demo_client, demo_transcript,
                 advisor_name="A", meeting_date="2026-11-10", **kw)


def test_polish_keeps_structure_and_rejects_unsafe(monkeypatch, fake_settings, demo_extraction, demo_flags,
                                                   demo_client, demo_transcript):
    base = _base(demo_extraction, demo_flags, demo_client, demo_transcript)
    sents = [s for sec in base.sections for s in sec.sentences if s.kind != "boilerplate"]
    good, bad = sents[0], next(s for s in sents if "30 000 €" in s.text)

    def fake_complete(system, user, schema, **_):
        assert good.id in user and "Responde" not in user
        return _Rewrites(sentences=[_Rewrite(id=good.id, text="Texto reescrito " + good.text),
                                    _Rewrite(id=bad.id, text=bad.text.replace("30 000", "40 000")),
                                    _Rewrite(id="p999", text="frase inventada")])

    monkeypatch.setattr("app.engine.llm.complete_json", fake_complete)
    out = _base(demo_extraction, demo_flags, demo_client, demo_transcript, polish=True, settings=fake_settings)

    flat = {s.id: s for sec in out.sections for s in sec.sentences}
    orig = {s.id: s for sec in base.sections for s in sec.sentences}
    assert flat.keys() == orig.keys()
    assert flat[good.id].text.startswith("Texto reescrito")
    assert flat[bad.id].text == bad.text  # changed amount -> template kept
    for sid, s in flat.items():
        o = orig[sid]
        assert (s.kind, s.evidence, s.flag_ids, s.status) == (o.kind, o.evidence, o.flag_ids, o.status)
        if s.kind == "boilerplate":
            assert s.text == o.text
    assert out.coverage_pct == base.coverage_pct and out.model.startswith("plantilla+")


def test_polish_falls_back_to_template_on_llm_error(monkeypatch, fake_settings, demo_extraction, demo_flags,
                                                     demo_client, demo_transcript):
    def boom(*_, **__):
        raise LLMError("sin red")

    monkeypatch.setattr("app.engine.llm.complete_json", boom)
    out = _base(demo_extraction, demo_flags, demo_client, demo_transcript, polish=True, settings=fake_settings)
    assert out == _base(demo_extraction, demo_flags, demo_client, demo_transcript)
    assert out.model == "plantilla" and report_mod.PROMPT.exists()
