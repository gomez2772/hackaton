"""Orchestrator: stt -> extract -> validate -> check -> report. Owner: B. Task B-04.

Respects ACTA_FAKE_STAGES so any stage can return the golden fixture.
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

from app import fakes
from app.config import STAGES, Settings, get_settings
from app.schemas import AnalysisResult, ClientProfile, StageTiming

log = logging.getLogger(__name__)


def analyze(audio_path: Path | None, client: ClientProfile, *,
            settings: Settings | None = None,
            on_stage: Callable[[str], None] | None = None,
            advisor_name: str | None = None,
            meeting_date: str | None = None) -> AnalysisResult:
    """Run the full pipeline and return everything the UI/API/exporters need."""
    s = settings or get_settings()
    timings: list[StageTiming] = []
    warnings: list[str] = []

    def stage(name: str, fake: bool, fn: Callable[[], object]) -> object:
        if on_stage:
            on_stage(name)
        t0 = time.perf_counter()
        out = fn()
        timings.append(StageTiming(stage=name, seconds=round(time.perf_counter() - t0, 3), fake=fake))
        return out

    # 1. STT
    if s.is_fake("stt") or audio_path is None:
        transcript = stage("stt", True, fakes.transcript)
    else:
        from app.audio.stt import transcribe
        transcript = stage("stt", False, lambda: transcribe(Path(audio_path)))

    # 2-3. Extraction + citation validation
    if s.is_fake("extract"):
        extraction = stage("extract", True, fakes.extraction)
        stage("validate", True, lambda: None)
    else:
        from app.engine.citations import validate
        from app.engine.extraction import extract
        raw = stage("extract", False, lambda: extract(transcript, client))
        extraction = stage("validate", False, lambda: validate(raw, transcript))

    # 4. Quantitative checker
    if s.is_fake("check"):
        flags = stage("check", True, fakes.flags)
    else:
        from app.engine.checker import check
        flags = stage("check", False, lambda: check(extraction, client))

    # 5. Report
    if s.is_fake("report"):
        report = stage("report", True, fakes.report)
    else:
        from app.engine.report import draft
        report = stage("report", False, lambda: draft(
            extraction, flags, client, transcript,
            advisor_name=advisor_name or s.advisor_name,
            meeting_date=meeting_date or date.today().isoformat(),
        ))
        # TODO(B-04): catch LLMError here -> template_mode report + warning.

    return AnalysisResult(
        analysis_id=f"AN-{uuid.uuid4().hex[:12]}", client=client, transcript=transcript,
        extraction=extraction, flags=flags, report=report, timings=timings, warnings=warnings,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Ejecuta el pipeline de Acta")
    ap.add_argument("audio", nargs="?", type=Path)
    ap.add_argument("--client", default="CLI-DEMO-001")
    ap.add_argument("--fake", action="store_true", help="todas las etapas simuladas")
    ap.add_argument("--out", type=Path, help="guarda el AnalysisResult en JSON")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    settings = get_settings(fake_stages=frozenset(STAGES)) if args.fake else get_settings()
    from app.data.loaders import load_client
    result = analyze(args.audio, load_client(args.client), settings=settings,
                     on_stage=lambda st: log.info("etapa: %s", st))
    log.info("análisis %s · %d banderas · cobertura %.1f %%",
             result.analysis_id, len(result.flags), result.report.coverage_pct)
    if args.out:
        args.out.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        log.info("guardado en %s", args.out)


if __name__ == "__main__":
    main()
