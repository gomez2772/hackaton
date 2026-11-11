"""Evaluation of Verbatim on the 5 synthetic meetings (D-4). Owner: D.

Runs the real pipeline (`app.pipeline.analyze`) on each meeting in tests/eval/meetings/ and scores it
against truth.json: recommendations, stated needs, flags, conduct, literal quotes, coverage and latency.

Sources:
  --source script  transcript built from script.json (no ElevenLabs; spends Claude only).
                   Isolates the LLM stages from STT errors.
  --source audio   app/data/meetings/<id>/audio.mp3 (C-7) through ElevenLabs Scribe (cached by hash).

Usage:
  python tests/eval/run_eval.py --source script            # all 5, prints the table
  python tests/eval/run_eval.py --source audio --write-doc # also writes docs/EVAL.md
  python tests/eval/run_eval.py --source script --only m03_promesa_presion
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.engine.citations import normalize  # noqa: E402
from app.schemas import (  # noqa: E402
    AnalysisResult,
    ClientProfile,
    Evidence,
    FundKID,
    Recommendation,
    Segment,
    Transcript,
)

log = logging.getLogger("eval")
MEETINGS = ROOT / "tests" / "eval" / "meetings"
AUDIO = ROOT / "app" / "data" / "meetings"
RESULTS = ROOT / "tests" / "eval" / "results"
EVAL_DOC = ROOT / "docs" / "EVAL.md"
WORDS_PER_SECOND = 2.5  # Spanish speech, only to give script segments plausible timestamps
SEV_RANK = {"green": 0, "amber": 1, "red": 2}
CAVEATS = [
    "- **Muestra pequeña y sintética**: 5 reuniones de 1,5–2 min escritas por D con Claude y evaluadas con Claude.",
    "- **Posible contaminación**: los guiones están en el repositorio; si un prompt se ajusta viéndolos, las cifras se "
    "inflan. Comprobar que los prompts no copian frases de `tests/eval/meetings/`.",
    "- **`--source script` no incluye la transcripción real**: mide solo las etapas con LLM. La cifra de extremo a extremo "
    "es la de `--source audio`.",
]
KEYWORDS = [("emergente", "equity_em"), ("renta variable", "equity_global"), ("global", "equity_global"),
            ("monetari", "money_market"), ("renta fija", "bond_short_eur")]


# ----------------------------------------------------------------------------- meetings
@dataclass
class Meeting:
    id: str
    turns: list[tuple[str, str]]
    client: ClientProfile
    truth: dict


def load_meetings(only: str | None = None) -> list[Meeting]:
    """All meetings in tests/eval/meetings (or just `only`)."""
    out = []
    for d in sorted(p for p in MEETINGS.iterdir() if p.is_dir()):
        if only and d.name != only:
            continue
        script = json.loads((d / "script.json").read_text(encoding="utf-8"))
        out.append(Meeting(
            id=d.name,
            turns=[(who, text) for who, text in script["turns"]],
            client=ClientProfile.model_validate_json((d / "client.json").read_text(encoding="utf-8")),
            truth=json.loads((d / "truth.json").read_text(encoding="utf-8")),
        ))
    return out


def script_transcript(m: Meeting) -> Transcript:
    """Transcript straight from the script: speaker_0 = advisor, speaker_1 = client, estimated times."""
    segs, t = [], 0.0
    for i, (who, text) in enumerate(m.turns):
        dur = max(1.5, len(text.split()) / WORDS_PER_SECOND)
        segs.append(Segment(id=f"s{i:04d}", speaker_id="speaker_0" if who == "advisor" else "speaker_1",
                            start=round(t, 2), end=round(t + dur, 2), text=text))
        t += dur + 0.3
    return Transcript(audio_id=hashlib.sha256(m.id.encode()).hexdigest()[:16], duration_s=round(t, 2),
                      segments=segs, stt_provider="fixture")


def run_meeting(m: Meeting, source: str) -> AnalysisResult:
    """Run the real pipeline on one meeting."""
    from app.pipeline import analyze

    settings = get_settings(fake_stages=frozenset())
    client = m.client  # real catalogue ISINs (C-3), see tests/eval/meetings/README.md
    if source == "audio":
        audio = AUDIO / m.id / "audio.mp3"
        if not audio.exists():
            raise FileNotFoundError(f"falta {audio.relative_to(ROOT)} (tarea C-7)")
        return analyze(audio, client, settings=settings, meeting_date="2026-11-11")
    transcript = script_transcript(m)
    with mock.patch("app.audio.stt.transcribe", lambda *_a, **_k: transcript):
        return analyze(Path(f"{m.id}.script"), client, settings=settings, meeting_date="2026-11-11")


# ----------------------------------------------------------------------------- scoring
def asset_class(rec: Recommendation, kids: dict[str, FundKID]) -> str | None:
    """Asset class of a predicted recommendation: from its ISIN, else from keywords in its name."""
    if rec.isin and rec.isin in kids:
        return kids[rec.isin].asset_class
    name = normalize(f"{rec.product_name} {rec.rationale}")
    return next((cls for kw, cls in KEYWORDS if normalize(kw) in name), None)


def prf(tp: int, fp: int, fn: int) -> dict[str, float | None]:
    """Precision, recall and F1 (None when undefined)."""
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f1 = 2 * p * r / (p + r) if p and r else (0.0 if p is not None and r is not None else None)
    return {"precision": p, "recall": r, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def score_recommendations(truth: list[dict], pred: list[Recommendation], kids: dict[str, FundKID]) -> dict:
    """Match by (action, asset class); also report whether matched amounts are right (±1 %)."""
    left = [(r.action, asset_class(r, kids), r.amount_eur) for r in pred]
    tp = amount_ok = 0
    for t in truth:
        hit = next((p for p in left if p[0] == t["action"] and p[1] == t["asset_class"]), None)
        if hit:
            left.remove(hit)
            tp += 1
            amount_ok += hit[2] is not None and abs(hit[2] - t["amount_eur"]) <= 0.01 * t["amount_eur"]
    return {**prf(tp, len(left), len(truth) - tp), "amount_ok": amount_ok}


def score_needs(truth: list[dict], pred: list) -> dict:
    """Stated needs matched by kind (multiset)."""
    kinds = [n.kind for n in pred]
    tp = 0
    for t in truth:
        if t["kind"] in kinds:
            kinds.remove(t["kind"])
            tp += 1
    return prf(tp, len(kinds), len(truth) - tp)


def score_flags(truth: dict[str, str | None], flags: list) -> dict:
    """Severity per flag type (worst if several) vs truth; `null` truth is not scored."""
    got: dict[str, str] = {}
    for f in flags:
        t, sev = f.type.value, f.severity.value
        if t not in got or SEV_RANK[sev] > SEV_RANK[got[t]]:
            got[t] = sev
    scored = {k: v for k, v in truth.items() if v is not None}
    hits = {k: got.get(k) == v for k, v in scored.items()}
    red_tp = sum(v == "red" and got.get(k) == "red" for k, v in scored.items())
    red_fp = sum(v != "red" and got.get(k) == "red" for k, v in scored.items())
    red_fn = sum(v == "red" and got.get(k) != "red" for k, v in scored.items())
    return {"correct": sum(hits.values()), "total": len(hits), "detail": {k: [scored[k], got.get(k)] for k in scored},
            "red": prf(red_tp, red_fp, red_fn)}


def score_conduct(truth: dict, conduct) -> dict:
    """Status per checklist code; `conduct_acceptable` widens what counts as right. Breach P/R."""
    if conduct is None:
        return {"correct": 0, "total": len(truth["conduct"]), "missing": True, "detail": {},
                "breach": prf(0, 0, sum(v == "breach" for v in truth["conduct"].values()))}
    got = {it.code: it.status.value for it in conduct.items}
    ok_sets = {c: set(truth.get("conduct_acceptable", {}).get(c, [s])) for c, s in truth["conduct"].items()}
    hits = {c: got.get(c) in ok_sets[c] for c in ok_sets}
    tp = sum(truth["conduct"][c] == "breach" and got.get(c) == "breach" for c in ok_sets)
    fp = sum(got.get(c) == "breach" and "breach" not in ok_sets[c] for c in ok_sets)
    fn = sum(truth["conduct"][c] == "breach" and got.get(c) != "breach" for c in ok_sets)
    return {"correct": sum(hits.values()), "total": len(hits), "missing": False,
            "detail": {c: [truth["conduct"][c], got.get(c), hits[c]] for c in ok_sets}, "breach": prf(tp, fp, fn)}


def all_evidence(r: AnalysisResult) -> list[Evidence]:
    """Every quote produced by the LLM stages (extraction, conduct, client summary)."""
    x = r.extraction
    evs = [e for grp in (x.circumstance_changes, x.stated_needs, x.recommendations, x.commitments)
           for it in grp for e in it.evidence]
    if r.conduct:
        evs += [e for it in r.conduct.items for e in it.evidence]
    if r.client_summary:
        evs += [e for p in r.client_summary.points + r.client_summary.next_steps for e in p.evidence]
    return evs


def quote_forms(q: str | list[str]) -> list[str]:
    """A key quote is a string or a list of accepted forms (script wording, real-transcript wording)."""
    return [q] if isinstance(q, str) else list(q)


def score_quotes(key_quotes: list[str | list[str]], evs: list[Evidence]) -> dict:
    """Key-quote recall (a verified quote overlaps any accepted form) and share of verified quotes."""
    ver = [normalize(e.quote) for e in evs if e.verified]

    def hit(form: str) -> bool:
        f = normalize(form)
        return any(f in v or (len(v.split()) >= 3 and v in f) for v in ver)

    found = [q for q in key_quotes if any(hit(f) for f in quote_forms(q))]
    return {"key_found": len(found), "key_total": len(key_quotes),
            "missing": [quote_forms(q)[0] for q in key_quotes if q not in found],
            "verified": len(ver), "evidence_total": len(evs)}


def score(m: Meeting, r: AnalysisResult, kids: dict[str, FundKID]) -> dict:
    """All metrics for one meeting."""
    t = m.truth
    return {
        "meeting": m.id, "scenario": t["scenario"],
        "recommendations": score_recommendations(t["recommendations"], r.extraction.recommendations, kids),
        "needs": score_needs(t["stated_needs"], r.extraction.stated_needs),
        "flags": score_flags(t["flags"], r.flags),
        "conduct": score_conduct(t, r.conduct),
        "quotes": score_quotes(t["key_quotes"], all_evidence(r)),
        "coverage_pct": r.report.coverage_pct,
        "template_mode": r.report.template_mode,
        "truth_revisions": t.get("truth_revisions", []),
        "timings": {tm.stage: tm.seconds for tm in r.timings},
        "warnings": r.warnings,
    }


# ----------------------------------------------------------------------------- aggregate and report
def _sum_prf(rows: list[dict]) -> dict:
    return prf(sum(x["tp"] for x in rows), sum(x["fp"] for x in rows), sum(x["fn"] for x in rows))


def aggregate(scores: list[dict]) -> dict:
    """Micro-averaged totals across meetings."""
    stages = sorted({s for sc in scores for s in sc["timings"]})
    return {
        "meetings": len(scores),
        "recommendations": _sum_prf([s["recommendations"] for s in scores]),
        "amount_ok": sum(s["recommendations"]["amount_ok"] for s in scores),
        "needs": _sum_prf([s["needs"] for s in scores]),
        "flags_correct": sum(s["flags"]["correct"] for s in scores),
        "flags_total": sum(s["flags"]["total"] for s in scores),
        "red_flags": _sum_prf([s["flags"]["red"] for s in scores]),
        "conduct_correct": sum(s["conduct"]["correct"] for s in scores),
        "conduct_total": sum(s["conduct"]["total"] for s in scores),
        "breaches": _sum_prf([s["conduct"]["breach"] for s in scores]),
        "key_quotes_found": sum(s["quotes"]["key_found"] for s in scores),
        "key_quotes_total": sum(s["quotes"]["key_total"] for s in scores),
        "quotes_verified": sum(s["quotes"]["verified"] for s in scores),
        "quotes_total": sum(s["quotes"]["evidence_total"] for s in scores),
        "coverage_mean": mean(s["coverage_pct"] for s in scores) if scores else None,
        "latency_mean": {st: mean(s["timings"].get(st, 0.0) for s in scores) for st in stages},
        "latency_total_mean": mean(sum(s["timings"].values()) for s in scores) if scores else None,
    }


def real_latency(agg: dict, source: str) -> tuple[dict, float | None, str]:
    """Latencies to report. A stage served from the LLM cache measures ~0 s, so for each such stage
    reuse the latest saved run of the same source where that stage really called the API."""
    LLM = ("extract", "conduct")  # summary runs in parallel with conduct; report/check are local
    current = dict(agg["latency_mean"])
    cached = [st for st in LLM if current.get(st, 0.0) < 0.5]
    if not cached:
        return current, agg["latency_total_mean"], ""
    sources = []
    for f in sorted(RESULTS.glob(f"{source}-*.json"), reverse=True):
        prev = json.loads(f.read_text(encoding="utf-8"))["aggregate"]["latency_mean"]
        for st in list(cached):
            if prev.get(st, 0.0) >= 0.5:
                current[st] = prev[st]
                cached.remove(st)
                sources.append(f"{st}: `{f.name}`")
        if not cached:
            break
    total = sum(current.values()) if not cached else None
    return current, total, "; ".join(sources)


def pct(x: float | None) -> str:
    """0.873 -> '87,3 %' ; None -> '—'."""
    return "—" if x is None else f"{100 * x:.1f} %".replace(".", ",")


def frac(a: int, b: int) -> str:
    """'7/8 (87,5 %)'."""
    return f"{a}/{b} ({pct(a / b if b else None)})"


def secs(x: float | None) -> str:
    return "—" if x is None else f"{x:.1f} s".replace(".", ",")


def markdown(scores: list[dict], agg: dict, source: str, model: str) -> str:
    """docs/EVAL.md body."""
    rec, needs, red, br = agg["recommendations"], agg["needs"], agg["red_flags"], agg["breaches"]
    lat_stage, lat_total, lat_src = real_latency(agg, source)
    lat_note = f" (etapas en caché: latencia de su última ejecución real, {lat_src})" if lat_src else ""
    src = ("transcripción del guion (sin STT)" if source == "script"
           else "audio sintético (TTS) → ElevenLabs Scribe")
    lines = [
        "# EVAL.md — Evaluación de Verbatim (D-4)",
        "",
        f"Generado por `tests/eval/run_eval.py --source {source}` el {datetime.now():%Y-%m-%d %H:%M}. "
        f"Modelo: `{model}`. Entrada: {src}.",
        f"Datos: {agg['meetings']} reuniones **sintéticas** de ~1,5–2 min (`tests/eval/meetings/`): 2 con conflicto de "
        "idoneidad, 2 con fallos de conducta y 1 correcta. Muestra pequeña: las cifras son orientativas.",
        "",
        "## Resumen",
        "",
        "| Métrica | Resultado |",
        "|---------|-----------|",
        f"| Recomendaciones: precisión · exhaustividad | {pct(rec['precision'])} · {pct(rec['recall'])} |",
        f"| Importe correcto en recomendaciones detectadas | {frac(agg['amount_ok'], rec['tp'])} |",
        f"| Necesidades declaradas: precisión · exhaustividad | {pct(needs['precision'])} · {pct(needs['recall'])} |",
        f"| Banderas con la severidad esperada | {frac(agg['flags_correct'], agg['flags_total'])} |",
        f"| Banderas rojas: precisión · exhaustividad | {pct(red['precision'])} · {pct(red['recall'])} |",
        f"| Conducta: estado correcto por comprobación | {frac(agg['conduct_correct'], agg['conduct_total'])} |",
        f"| Incumplimientos de conducta: precisión · exhaustividad | {pct(br['precision'])} · {pct(br['recall'])} |",
        f"| Citas clave encontradas | {frac(agg['key_quotes_found'], agg['key_quotes_total'])} |",
        f"| Citas del LLM verificadas literalmente | {frac(agg['quotes_verified'], agg['quotes_total'])} |",
        f"| Cobertura media del informe | {pct(agg['coverage_mean'] / 100 if agg['coverage_mean'] is not None else None)} |",
        f"| Latencia media total | {secs(lat_total)}{lat_note} |",
        "",
        "Latencia media por etapa: " + " · ".join(f"{k} {secs(v)}" for k, v in lat_stage.items()
                                                    if v >= 0.05) + " (el resumen va en paralelo con la conducta).",
        "",
        "## Por reunión",
        "",
        "| Reunión | Escenario | Recos | Banderas | Conducta | Citas clave | Cobertura | Avisos |",
        "|---------|-----------|-------|----------|----------|-------------|-----------|--------|",
    ]
    for s in scores:
        r = s["recommendations"]
        lines.append(
            f"| {s['meeting']} | {s['scenario']} | {r['tp']}/{r['tp'] + r['fn']} (+{r['fp']} FP) | "
            f"{s['flags']['correct']}/{s['flags']['total']} | {s['conduct']['correct']}/{s['conduct']['total']} | "
            f"{s['quotes']['key_found']}/{s['quotes']['key_total']} | {pct(s['coverage_pct'] / 100)} | "
            f"{len(s['warnings'])} |")
    lines += ["", "## Fallos (para B-5)", ""]
    fails = []
    for s in scores:
        for k, (exp, got) in s["flags"]["detail"].items():
            if exp != got:
                fails.append(f"- {s['meeting']} · bandera `{k}`: esperado {exp}, obtenido {got}")
        for k, (exp, got, ok) in s["conduct"]["detail"].items():
            if not ok:
                fails.append(f"- {s['meeting']} · conducta `{k}`: esperado {exp}, obtenido {got}")
        fails += [f"- {s['meeting']} · cita clave no encontrada: «{q}»" for q in s["quotes"]["missing"]]
        fails += [f"- {s['meeting']} · aviso: {w}" for w in s["warnings"]]
    lines += fails or ["Ninguno."]
    revisions = [f"- {s['meeting']} · {rev}" for s in scores for rev in s.get("truth_revisions", [])]
    if revisions:
        lines += ["", "## Revisiones de la verdad de referencia", "",
                  "Cambios hechos en `truth.json` después de ver resultados; se declaran para no maquillar cifras.", ""]
        lines += revisions
    lines += ["", "## Advertencias", "", *CAVEATS]
    lines += ["", "Detalle completo en `tests/eval/results/`.", ""]
    return "\n".join(lines)


SOURCE_TITLE = {
    "audio": "Con audio: audios sintéticos (TTS) → transcripción real de ElevenLabs Scribe → pipeline",
    "script": "Con guion: transcripción construida a partir del guion (aísla las etapas con LLM)",
}


def latest_result(source: str) -> dict | None:
    """Most recent saved result of `source` (tests/eval/results/<source>-*.json)."""
    files = sorted(RESULTS.glob(f"{source}-*.json"))
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def combined_doc() -> str:
    """docs/EVAL.md with every source that has results: audio first (end to end), then script."""
    parts = []
    for source in ("audio", "script"):
        r = latest_result(source)
        if r is None:
            continue
        body = markdown(r["meetings"], r["aggregate"], source, r["model"]).split("\n")
        body = [("#" + line if line.startswith("## ") else line) for line in body[1:]]  # drop title, demote
        parts.append("\n".join([f"## {SOURCE_TITLE[source]}", *body]))
    head = ["# EVAL.md — Evaluación de Verbatim (D-4)", "",
            "Regenerar: `python tests/eval/run_eval.py --source audio --write-doc` (o `--source script`). "
            "Cada sección usa el último resultado guardado de esa fuente.", ""]
    return "\n".join(head) + "\n" + "\n\n".join(parts) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Evalúa Verbatim sobre las reuniones sintéticas")
    ap.add_argument("--source", choices=["script", "audio"], default="script")
    ap.add_argument("--only", help="id de una reunión (carpeta)")
    ap.add_argument("--write-doc", action="store_true", help="escribe docs/EVAL.md")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    from app.data.loaders import load_kids

    kids = load_kids()
    meetings = load_meetings(args.only)
    scores = []
    for m in meetings:
        log.info("reunión %s (%s)…", m.id, args.source)
        r = run_meeting(m, args.source)
        scores.append(score(m, r, kids))
    agg = aggregate(scores)
    model = get_settings().anthropic_model
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{args.source}-{datetime.now():%Y%m%d-%H%M}.json"
    out.write_text(json.dumps({"source": args.source, "model": model, "aggregate": agg, "meetings": scores},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    doc = markdown(scores, agg, args.source, model)
    sys.stdout.write(doc + "\n")
    log.info("resultados en %s", out.relative_to(ROOT))
    if args.write_doc:
        EVAL_DOC.write_text(combined_doc(), encoding="utf-8")
        log.info("escrito %s", EVAL_DOC.relative_to(ROOT))


if __name__ == "__main__":
    main()
