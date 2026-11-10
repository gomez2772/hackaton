"""Exporters (A-06): the demo result in the five formats."""

from __future__ import annotations

import io

import pytest

from app.export import FORMATS, export


@pytest.mark.parametrize("fmt", list(FORMATS))
def test_export_all_formats(demo_result, fmt):
    data = export(demo_result, fmt)
    assert len(data) > 500
    if fmt == "pdf":
        assert data.startswith(b"%PDF")
    if fmt == "docx":
        from docx import Document

        text = "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
        assert "Informe de idoneidad" in text and "NO CUMPLE" in text
    if fmt in ("md", "html"):
        txt = data.decode()
        assert "Conducta durante la reunión" in txt and "Resumen para el cliente" in txt
