"""Local regulation base (app/data/normativa): documents, checklist and prompt blocks."""

from __future__ import annotations

from app.data import regulation as reg
from app.schemas import FlagType


def test_documents_and_checklist_load():
    docs = reg.load_documents()
    assert docs.count("<documento ") == 4
    ids = [r["id"] for r in reg.load_checklist()]
    assert len(ids) == len(set(ids)) >= 30
    for r in reg.load_checklist():
        assert (reg.DIR / r["documento"]).exists(), r["id"]
        assert r["tipo_comprobacion"] in {"codigo", "llm", "asesor"}


def test_lookup_and_hallucinated_ids():
    assert reg.requirement("IDO-08")["fuente"].startswith("Reglamento Delegado 2017/565")
    assert {r["id"] for r in reg.requirements_by_block("costes")} == {"COS-01"}
    assert reg.invalid_references("Ver IDO-08, AJU-01 y IDO-99") == ["IDO-99"]


def test_every_flag_type_maps_to_existing_requirements():
    assert set(reg.FLAG_REQUIREMENTS) == {t.value for t in FlagType}
    for ids in reg.FLAG_REQUIREMENTS.values():
        assert set(ids) <= reg.valid_ids()


def test_system_blocks_cache_the_stable_prefix():
    a = reg.system_blocks("tarea A")
    b = reg.system_blocks("tarea B")
    assert a[0] == b[0] and a[0]["cache_control"] == {"type": "ephemeral"}
    assert a[1] == {"type": "text", "text": "tarea A"} and "cache_control" not in a[1]
    assert reg.system_blocks() == [a[0]]
