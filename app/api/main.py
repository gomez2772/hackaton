"""FastAPI app for GPTadvisor. Owner: A. Task A-07.

Run: uvicorn app.api.main:app --reload   ·   Docs: http://localhost:8000/docs
Contract: docs/CONTRACT.md §A·API REST.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.schemas import SCHEMA_VERSION

app = FastAPI(
    title="Acta API",
    version=SCHEMA_VERSION,
    description="Audio de la reunión → informe de idoneidad MiFID II trazable al segundo.",
)


@app.get("/v1/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "schema_version": SCHEMA_VERSION}


# TODO(A-07): X-API-Key dependency, GET /v1/clients, POST /v1/analyses (multipart),
# GET /v1/analyses/{id}, GET /v1/analyses/{id}/report?format=..., GET /v1/analyses/{id}/audio
