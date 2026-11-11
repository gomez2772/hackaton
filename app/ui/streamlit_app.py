"""Acta demo UI (Streamlit). Owner: A. Tasks A-1..A-7.

Run:  streamlit run app/ui/streamlit_app.py
Consumes only app.pipeline.analyze, app.data.loaders and app.export (CONTRACT §A·UI).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st  # noqa: E402

from app import fakes  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.data.loaders import list_clients  # noqa: E402
from app.export import FORMATS, SUMMARY_FORMATS, export, export_summary, summary_text  # noqa: E402
from app.pipeline import analyze  # noqa: E402
from app.schemas import AnalysisResult, Evidence  # noqa: E402
from app.ui.progress import STAGE_ORDER, StageProgress, save_audio, secs  # noqa: E402

st.set_page_config(page_title="Acta", page_icon="📝", layout="wide")
SEV = {"red": "🔴", "amber": "🟠", "green": "🟢"}
CONDUCT = {"ok": "🟢 Cumple", "breach": "🔴 No cumple", "no_evidence": "⚪ Sin evidencia"}
STAGE_LABEL = {"stt": "Transcribiendo", "extract": "Extrayendo con Claude", "validate": "Verificando citas",
               "check": "Comprobando idoneidad", "conduct": "Revisando la conducta", "summary": "Resumiendo para el cliente",
               "report": "Redactando el informe"}
STAGE_SHORT = {"stt": "Transcripción", "extract": "Extracción", "validate": "Citas", "check": "Idoneidad",
               "conduct": "Conducta", "summary": "Resumen", "report": "Informe"}
DEMO_CLIENT_ID = "CLI-DEMO-001"
TAGLINE = ("Del audio de la reunión al informe de idoneidad MiFID II, con cada frase enlazada "
           "al segundo exacto del audio en que se dijo.")
settings = get_settings()
st.session_state.setdefault("t", 0)


def eur(x: float) -> str:
    """100000.0 -> '100 000 €'."""
    return f"{x:,.0f} €".replace(",", " ")


def sync_demo_param() -> None:
    """Keep ?demo=1 in the URL in sync with the toggle, so a refresh or a bookmark keeps demo mode."""
    if st.session_state.get("demo_toggle"):
        st.query_params["demo"] = "1"
    else:
        st.query_params.pop("demo", None)


def request_run() -> None:
    """Main-area «Analizar» button: run on the next rerun (keeps the landing out of the results page)."""
    st.session_state.run_requested = True


def reset_analysis() -> None:
    """Back to the landing page (between rehearsals)."""
    for k in ("result", "audio", "exports", "edits"):
        st.session_state.pop(k, None)
    st.session_state.t = 0


def mmss(t: float | None) -> str:
    t = int(t or 0)
    return f"{t // 60:02d}:{t % 60:02d}"


def speaker_label(role: str, speaker_id: str) -> str:
    """Readable speaker name; unknown roles become 'Hablante N'."""
    if role == "advisor":
        return "🧑‍💼 Asesor"
    if role == "client":
        return "🙋 Cliente"
    digits = "".join(ch for ch in speaker_id if ch.isdigit())
    return f"🗣️ Hablante {int(digits) + 1}" if digits else f"🗣️ {speaker_id}"


def exported(res: AnalysisResult, fmt: str, kind: str = "report") -> bytes:
    """Export once per analysis: every ▶ click reruns the script and PDF/DOCX take ~0.4 s."""
    cache = st.session_state.setdefault("exports", {})
    key = (res.analysis_id, kind, fmt)
    if key not in cache:
        cache[key] = export(res, fmt) if kind == "report" else export_summary(res, fmt)
    return cache[key]


def jump(second: float | None) -> None:
    # on_click runs BEFORE the rerun, so the player is drawn at the right second
    st.session_state.t = int(second or 0)


def evidence_buttons(evs: list[Evidence], key: str) -> None:
    ok = [e for e in evs if e.verified]
    if not ok:
        st.caption(":orange[⚠ sin evidencia en el audio: el asesor debe confirmarlo]")
        return
    cols = st.columns(min(len(ok), 4) + 3)
    for i, e in enumerate(ok[:4]):
        cols[i].button(f"▶ {mmss(e.start)}", key=f"{key}-{i}", help=f"«{e.quote}»", on_click=jump, args=(e.start,))


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.title("📝 Acta")
    st.caption("Del audio de la reunión al informe de idoneidad MiFID II · para GPTadvisor")
    demo = st.toggle("Modo demo", value=st.query_params.get("demo") == "1", key="demo_toggle",
                     on_change=sync_demo_param,
                     help="Cliente y clip de la demo precargados y sin datos técnicos en pantalla. "
                          "También se activa abriendo la página con ?demo=1.")
    if settings.fake_stages and not demo:
        st.info(f"Etapas simuladas: {', '.join(sorted(settings.fake_stages))}")
    clients = list_clients()
    demo_index = next((i for i, c in enumerate(clients) if c.client_id == DEMO_CLIENT_ID), 0)
    client = st.selectbox("Cliente", clients, index=demo_index,
                          format_func=lambda c: f"{c.name} · perfil {c.risk_profile}")
    source = st.radio("Audio", ["Clip de la demo", "Grabar ahora", "Subir archivo"], horizontal=False)
    audio_bytes, audio_name = None, None
    if source == "Grabar ahora":
        rec = st.audio_input("Graba la reunión (con el consentimiento del cliente)")
        if rec:
            audio_bytes, audio_name = rec.getvalue(), "grabacion.wav"
    elif source == "Subir archivo":
        up = st.file_uploader("Audio", type=["mp3", "wav", "m4a", "webm", "ogg"])
        if up:
            audio_bytes, audio_name = up.getvalue(), up.name
    needs_audio = source != "Clip de la demo"
    if needs_audio and audio_bytes and settings.is_fake("stt"):
        st.caption(":orange[Transcripción simulada: se analizará la reunión de ejemplo, no tu audio.]")
    advisor = st.text_input("Asesor", settings.advisor_name)
    go = st.button("Analizar", type="primary", use_container_width=True, disabled=needs_audio and not audio_bytes)
    if needs_audio and not audio_bytes:
        st.caption("Graba o sube un audio para poder analizarlo.")

go = go or st.session_state.pop("run_requested", False)
st.markdown("#### 📝 Acta :gray[· para GPTadvisor]")

if go:
    if audio_bytes:
        audio_path: Path | None = save_audio(audio_bytes, audio_name, settings.cache_dir / "uploads")
    else:
        audio_path = fakes.demo_audio()  # None -> the pipeline uses the fixture transcript
    prog = StageProgress()
    with st.status("Analizando la reunión…", expanded=True) as status:
        bar = st.progress(0.0)
        board = st.empty()

        def on_stage(stage: str) -> None:
            prog.start(stage)
            n = STAGE_ORDER.index(stage) + 1 if stage in STAGE_ORDER else len(prog.done) + 1
            bar.progress(prog.fraction, text=f"{STAGE_LABEL.get(stage, stage)}… ({n}/{len(STAGE_ORDER)})")
            board.markdown(prog.markdown(STAGE_LABEL))

        try:
            result = analyze(audio_path, client, settings=settings, advisor_name=advisor, on_stage=on_stage)
        except Exception as e:  # STT (or another stage without fallback) failed: say so, don't show a traceback
            prog.fail()
            board.markdown(prog.markdown(STAGE_LABEL))
            status.update(label=f"El análisis falló en «{STAGE_SHORT.get(prog.failed or '', '?')}»",
                          state="error", expanded=True)
            st.error(f"No se pudo completar el análisis: {e}")
            st.session_state.pop("result", None)
            st.stop()
        prog.finish()
        bar.progress(1.0, text=f"{len(STAGE_ORDER)}/{len(STAGE_ORDER)} etapas")
        board.markdown(prog.markdown(STAGE_LABEL))
        total = sum(t.seconds for t in result.timings)
        status.update(label=f"Análisis completado en {secs(total)}", state="complete", expanded=False)
    st.session_state.result, st.session_state.audio, st.session_state.t = result, audio_path, 0
    st.session_state.exports = {}

res: AnalysisResult | None = st.session_state.get("result")
if res is None:  # landing page: never an empty screen (A-7)
    st.markdown("## De la reunión al informe de idoneidad, en minutos")
    st.write(TAGLINE)
    s1, s2, s3 = st.columns(3)
    s1.markdown("**1 · Graba o sube la llamada**  \nCon el consentimiento del cliente.")
    s2.markdown("**2 · Analiza**  \nTranscripción, extracción con citas, idoneidad y conducta.")
    s3.markdown("**3 · Revisa y exporta**  \nInforme MiFID II enlazado al audio y resumen para el cliente.")
    with st.container(border=True):
        total = sum(h.amount_eur for h in client.portfolio)
        st.markdown(f"**{client.name}** · perfil de riesgo {client.risk_profile} de 5"
                    + (f" · cartera {eur(total)}" if total else ""))
        if client.portfolio:
            st.caption(" · ".join(f"{h.name}: {eur(h.amount_eur)}" for h in client.portfolio))
        label = "▶ Analizar la reunión de demostración" if not needs_audio else "▶ Analizar"
        st.button(label, type="primary", on_click=request_run, disabled=needs_audio and not audio_bytes,
                  key="run-main")
        if not demo:
            st.caption("También puedes elegir otro cliente, grabar o subir un audio en la barra lateral.")
    st.caption("Clientes, carteras y reuniones de esta demostración son sintéticos.")
    st.stop()

# drawn after the analysis block so it appears right after the first «Analizar», not one rerun later
st.sidebar.button("↺ Nuevo análisis", on_click=reset_analysis, use_container_width=True, key="reset")

for w in res.warnings:
    st.warning(w)

# ------------------------------------------------------------------ player + headline
audio_path = st.session_state.get("audio")
if audio_path and Path(audio_path).exists():
    st.audio(str(audio_path), start_time=st.session_state.t)
    st.caption(f"Reproduciendo desde {mmss(st.session_state.t)} · pulsa ▶ en cualquier frase para saltar a ese momento")
elif demo:
    st.caption("Audio no disponible en esta demostración: cada ▶ indica el minuto exacto de la cita.")
else:
    st.caption(f"(Sin audio en esta demostración simulada · salto pedido a {mmss(st.session_state.t)})")

reds = sum(f.severity.value == "red" for f in res.flags)
ambers = sum(f.severity.value == "amber" for f in res.flags)
breaches = sum(it.status.value == "breach" for it in res.conduct.items) if res.conduct else 0
c1, c2, c3, c4 = st.columns(4)
c1.metric("Idoneidad", "Sin evaluar" if not res.flags else "No idóneo" if reds else "Con advertencias" if ambers else "Idóneo")
c2.metric("Alertas rojas", reds)
c3.metric("Incumplimientos de conducta", breaches if res.conduct else "—",
          help=None if res.conduct else "El chequeo de conducta no está disponible para este análisis")
c4.metric("Cobertura de evidencia", "—" if res.report.template_mode else f"{res.report.coverage_pct:.0f} %")
if not (demo and all(t.fake for t in res.timings)):  # in demo mode, simulated 0,0 s timings are just noise
    st.caption(f"⏱ Total {secs(sum(t.seconds for t in res.timings))} — "
               + " · ".join(f"{STAGE_SHORT.get(t.stage, t.stage)} {secs(t.seconds)}" + (" (sim.)" if t.fake else "")
                            for t in res.timings))

t_rep, t_flags, t_cond, t_tr, t_sum = st.tabs(
    ["Informe de idoneidad", "Banderas", "Conducta", "Transcripción", "Resumen para el cliente"])

with t_rep:
    if res.report.template_mode:
        st.warning("Modo plantilla: la extracción con IA falló; completa el informe a mano.")
    for si, sec in enumerate(res.report.sections):
        st.subheader(sec.title)
        for pi, s in enumerate(sec.sentences):
            flag_marks = " ".join(SEV[f.severity.value] for f in res.flags if f.id in s.flag_ids)
            st.markdown(f"{s.text} {flag_marks}")
            if s.kind == "claim":
                evidence_buttons(s.evidence, f"rep-{si}-{pi}")
    st.divider()
    cols = st.columns(len(FORMATS))
    for col, fmt in zip(cols, FORMATS, strict=True):
        col.download_button(fmt.upper(), exported(res, fmt), file_name=f"informe_{res.analysis_id}.{fmt}",
                            mime=FORMATS[fmt], use_container_width=True)

with t_flags:
    if not res.flags:
        st.info("El comprobador no ha generado banderas: no se detectaron recomendaciones que evaluar.")
    order = {"red": 0, "amber": 1, "green": 2}
    for f in sorted(res.flags, key=lambda f: order[f.severity.value]):
        st.markdown(f"{SEV[f.severity.value]} **{f.title}** — {f.explanation}")
        if f.evidence:
            evidence_buttons(f.evidence, f"flag-{f.id}")

with t_cond:
    st.caption("Ayuda para el equipo de cumplimiento; no sustituye una revisión jurídica.")
    if not res.conduct:
        st.info("El chequeo de conducta no está disponible para este análisis.")
    else:
        for i, it in enumerate(res.conduct.items):
            st.markdown(f"**{CONDUCT[it.status.value]} · {it.title}** — {it.explanation}  \n_{it.rule}_")
            if it.evidence:
                evidence_buttons(it.evidence, f"cond-{i}")

with t_tr:
    cited = {e.segment_id for group in (res.extraction.circumstance_changes, res.extraction.stated_needs,
                                        res.extraction.recommendations, res.extraction.commitments)
             for item in group for e in item.evidence if e.verified}
    for seg in res.transcript.segments:
        who = speaker_label(seg.role.value, seg.speaker_id)
        a, b = st.columns([1, 9])
        a.button(mmss(seg.start), key=f"seg-{seg.id}", on_click=jump, args=(seg.start,))
        b.markdown(f"{who}: " + (f"**{seg.text}**" if seg.id in cited else seg.text))

with t_sum:
    if not res.client_summary:
        st.info("El resumen para el cliente no está disponible para este análisis.")
    else:
        cs = res.client_summary
        st.subheader(cs.title)
        for i, p in enumerate(cs.points):
            st.markdown(f"- {p.text}")
            evidence_buttons(p.evidence, f"sum-{i}")
        if cs.next_steps:
            st.markdown("**Próximos pasos**")
            for i, p in enumerate(cs.next_steps):
                st.markdown(f"- {p.text}")
                evidence_buttons(p.evidence, f"next-{i}")
        st.divider()
        st.markdown("**Enviar al cliente**")
        st.caption("Copia el texto con el icono 📋 de la esquina del recuadro y pégalo en un correo o mensaje, "
                   "o descárgalo como carta.")
        st.code(summary_text(res), language=None, wrap_lines=True)
        stem = f"resumen_{res.analysis_id}"
        labels = {"pdf": "📄 Carta PDF", "md": "Markdown"}
        cols = st.columns(len(labels) + 2)
        for col, (fmt, label) in zip(cols, labels.items(), strict=False):
            col.download_button(label, exported(res, fmt, kind="summary"), file_name=f"{stem}.{fmt}",
                                mime=SUMMARY_FORMATS[fmt], use_container_width=True, key=f"sum-dl-{fmt}")
