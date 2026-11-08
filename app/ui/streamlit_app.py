"""Acta demo UI (Streamlit). Owner: A. Tasks A-01..A-05, A-08, A-09.

Run:  streamlit run app/ui/streamlit_app.py
Minimal placeholder so H1 can be checked; A replaces it in A-01.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.data.loaders import list_clients  # noqa: E402
from app.pipeline import analyze  # noqa: E402

st.set_page_config(page_title="Acta", layout="wide")
st.title("Acta")
settings = get_settings()
st.caption(f"Etapas simuladas: {', '.join(sorted(settings.fake_stages)) or 'ninguna'}")

clients = list_clients()
client = st.selectbox("Cliente", clients, format_func=lambda c: f"{c.name} · perfil {c.risk_profile}")

if st.button("Analizar (modo simulado)"):
    result = analyze(None, client, settings=settings)
    cols = st.columns(3)
    cols[0].metric("Banderas rojas", sum(f.severity.value == "red" for f in result.flags))
    cols[1].metric("Cobertura de evidencia", f"{result.report.coverage_pct:.0f} %")
    cols[2].metric("Segmentos", len(result.transcript.segments))
    st.json(result.model_dump(mode="json"), expanded=False)
