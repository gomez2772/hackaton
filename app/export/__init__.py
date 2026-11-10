"""Report exporters: PDF, DOCX, Markdown, HTML, JSON. Owner: A. Task A-06.

Contract: docs/CONTRACT.md §A·Exportación.
"""

from __future__ import annotations

from typing import Literal

from app.schemas import AnalysisResult

Format = Literal["pdf", "docx", "md", "html", "json"]

FORMATS: dict[str, str] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md": "text/markdown; charset=utf-8",
    "html": "text/html; charset=utf-8",
    "json": "application/json",
}


def export(result: AnalysisResult, fmt: Format) -> bytes:
    """Serialize `result` in `fmt`."""
    if fmt == "json":
        return result.model_dump_json(indent=2).encode("utf-8")
    # TODO(A-06): md first (base for html via `markdown`), docx with python-docx, pdf with reportlab.
    raise NotImplementedError(f"A-06: exportación a {fmt} pendiente.")
