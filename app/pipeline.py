"""Orchestrator: stt -> extract -> validate -> check -> conduct -> summary -> report. Owner: B.

Respects ACTA_FAKE_STAGES so any stage can return the golden fixture.
Never raises because of the LLM: degrades (empty extraction / no conduct / no summary) and warns.
CLI:
    python -m app.pipeline --fake
    python -m app.pipeline path/to/audio.mp3 --client CLI-DEMO-001
"""

from __future__ import annotations

import argparse
import logging
import time
import uuid
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from app import fakes
from app.config import STAGES, Settings, get_settings
from app.schemas import AnalysisResult, ClientProfile, Extraction, Role, StageTiming, Transcript

log = logging.getLogger(__name__)


def analyze(audio_path: Path | None, client: ClientProfile, *,
            settings: Settings | None = None,
            on_stage: Callable[[str], None] | None = None,
            advisor_name: str | None = None,
            meeting_date: str | None = None,
            polish_report: bool = False) -> AnalysisResult:
    """Run the full pipeline and return everything the UI/API/exporters need.

    polish_report=True lets Claude rephrase the template report (B-6); falls back to the template.
    """
    s = settings or get_settings()
    timings: list[StageTiming] = []
    warnings: list[str] = []

    def stage(name: str, fake: bool, fn: Callable[[], Any], fallback: Callable[[], Any] | None = None) -> Any:
        if on_stage:
            on_stage(name)
        t0 = time.perf_counter()
        try:
            out = fn()
        except Exception as e:  # degrade instead of crashing the demo
            if fallback is None:
                raise
            log.exception("etapa %s falló", name)
            warnings.append(f"La etapa «{name}» falló ({type(e).__name__}: {str(e)[:160]}); resultado degradado.")
            out = fallback()
        timings.append(StageTiming(stage=name, seconds=round(time.perf_counter() - t0, 3), fake=fake))
        return out

    # 1. STT
    if s.is_fake("stt") or audio_path is None:
        transcript = stage("stt", True, fakes.transcript)
    else:
        from app.audio.stt import transcribe
        transcript = stage("stt", False, lambda: transcribe(Path(audio_path)))

    # 2-3. Extraction + citation validation
    from app.engine.citations import validate
    if s.is_fake("extract"):
        extraction = stage("extract", True, fakes.extraction)
        stage("validate", True, lambda: None)
    else:
        from app.engine.extraction import extract
        raw = stage("extract", False, lambda: extract(transcript, client, settings=s), fallback=Extraction)
        extraction = stage("validate", False, lambda: validate(raw, transcript))
    transcript = _apply_roles(transcript, extraction)
    template_mode = not s.is_fake("extract") and any("«extract»" in w for w in warnings)

    # 4. Quantitative checker
    if s.is_fake("check"):
        flags = stage("check", True, fakes.flags)
    else:
        from app.engine.checker import check
        flags = stage("check", False, lambda: check(extraction, client), fallback=list)

    # 5. Conduct («¿fue correcta la llamada?»)
    if s.is_fake("conduct"):
        conduct = stage("conduct", True, fakes.conduct)
    else:
        from app.engine.conduct import check_conduct
        conduct = stage("conduct", False, lambda: validate(check_conduct(transcript, extraction, settings=s), transcript),
                        fallback=lambda: None)

    # 6. Plain-language summary for the client
    if s.is_fake("summary"):
        summary = stage("summary", True, fakes.client_summary)
    else:
        from app.engine.summary import summarize
        summary = stage("summary", False, lambda: validate(summarize(transcript, extraction, settings=s), transcript),
                        fallback=lambda: None)

    # 7. Report
    if s.is_fake("report"):
        report = stage("report", True, fakes.report)
    else:
        from app.engine.report import draft
        report = stage("report", False, lambda: draft(
            extraction, flags, client, transcript,
            advisor_name=advisor_name or s.advisor_name,
            meeting_date=meeting_date or date.today().isoformat(),
            polish=polish_report and not template_mode, settings=s,
        ))
        if template_mode:
            report = report.model_copy(update={"template_mode": True})

    return AnalysisResult(
        analysis_id=f"AN-{uuid.uuid4().hex[:12]}", client=client, transcript=transcript,
        extraction=extraction, flags=flags, report=report, conduct=conduct, client_summary=summary,
        timings=timings, warnings=warnings,
    )


def _apply_roles(transcript: Transcript, extraction: Extraction) -> Transcript:
    """Fill Segment.role from extraction.speaker_roles (fallback: first speaker is the advisor)."""
    roles = dict(extraction.speaker_roles)
    if not roles and transcript.segments:
        order = list(dict.fromkeys(seg.speaker_id for seg in transcript.segments))
        roles = {sp: Role.ADVISOR if i == 0 else Role.CLIENT for i, sp in enumerate(order)}
    segs = [seg if seg.role != Role.UNKNOWN else seg.model_copy(update={"role": roles.get(seg.speaker_id, Role.UNKNOWN)})
            for seg in transcript.segments]
    return transcript.model_copy(update={"segments": segs})


def main() -> None:
    ap = argparse.ArgumentParser(description="Ejecuta el pipeline de Acta")
    ap.add_argument("audio", nargs="?", type=Path)
    ap.add_argument("--client", default="CLI-DEMO-001")
    ap.add_argument("--fake", action="store_true", help="todas las etapas simuladas")
    ap.add_argument("--out", type=Path, help="guarda el AnalysisResult en JSON")
    ap.add_argument("--pulir", action="store_true", help="redacta el informe con Claude sobre la plantilla (B-6)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    settings = get_settings(fake_stages=frozenset(STAGES)) if args.fake else get_settings()
    from app.data.loaders import load_client
    result = analyze(args.audio, load_client(args.client), settings=settings,
                     on_stage=lambda st: log.info("etapa: %s", st), polish_report=args.pulir)
    breaches = sum(it.status.value == "breach" for it in result.conduct.items) if result.conduct else 0
    log.info("análisis %s · %d banderas (%d rojas) · %d incumplimientos de conducta · cobertura %.1f %%",
             result.analysis_id, len(result.flags), sum(f.severity.value == "red" for f in result.flags),
             breaches, result.report.coverage_pct)
    for w in result.warnings:
        log.warning(w)
    if args.out:
        args.out.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        log.info("guardado en %s", args.out)


if __name__ == "__main__":
    main()
