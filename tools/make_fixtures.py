"""Regenerate the golden demo fixtures in fixtures/demo/ (owner: D).

Scenario (synthetic): Lucía, risk profile 3, retires in three years and needs 20 000 €
next year for her daughter's flat. The advisor proposes 30 000 € in an emerging-markets
equity fund and says she "won't lose money". Expected flags (= real checker): horizon RED, volatility RED (12,2 %, SRI approximation),
concentration AMBER, SRI AMBER (= profile max and she wants to preserve capital), liquidity GREEN. Expected conduct: return promise and risks not explained = breach;
costs and conflicts of interest = no evidence.

Run:  python tools/make_fixtures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.schemas import (  # noqa: E402
    AnalysisResult,
    CircumstanceChange,
    ClientProfile,
    ClientSummary,
    Commitment,
    ConductCheck,
    ConductItem,
    ConductStatus,
    Evidence,
    Extraction,
    Flag,
    FlagType,
    FundKID,
    Holding,
    Recommendation,
    ReportSection,
    ReportSentence,
    RiskProfileLimits,
    Role,
    Segment,
    Severity,
    StageTiming,
    StatedNeed,
    SuitabilityReport,
    SummaryPoint,
    Transcript,
)

OUT = ROOT / "fixtures" / "demo"

TURNS = [  # (speaker, start, end, text) — times from the real demo clip (C-2, Scribe)
    ("speaker_0", 0.1, 6.18, "Buenos días, Lucía. Antes de empezar, le recuerdo que esta reunión se graba con su consentimiento."),
    ("speaker_1", 7.24, 8.14, "Sí, sin problema."),
    ("speaker_0", 9.18, 17.56, "Perfecto. Revisando su cartera, tiene unos cien mil euros, la mayor parte en renta variable global y una parte en renta fija."),
    ("speaker_1", 18.6, 26.66, "Eso es. Le cuento una novedad: me jubilo en tres años, así que quiero ir pensando en tener el dinero disponible para entonces."),
    ("speaker_0", 27.7, 31.66, "Entendido, tres años. ¿Hay algún gasto importante antes de esa fecha?"),
    ("speaker_1", 32.78, 38.36, "Sí, lo de la entrada del piso de mi hija. Necesitaré unos veinte mil euros el año que viene."),
    ("speaker_0", 39.38, 49.22, "Tomo nota. Ahora mismo los mercados emergentes están baratos. Le propongo invertir treinta mil euros en un fondo indexado de renta variable emergente."),
    ("speaker_1", 50.22, 53.46, "Bueno, si usted lo ve bien... no entiendo mucho de esto."),
    ("speaker_0", 54.48, 62.92, "Es un fondo con buen potencial a largo plazo y con este no va a perder dinero. Lo financiaríamos vendiendo parte de la renta fija."),
    ("speaker_1", 63.94, 68.02, "Lo que no quiero es llevarme sustos, que con la jubilación tan cerca me pone nerviosa."),
    ("speaker_0", 69.02, 74.04, "Lo entiendo. Le enviaré por correo la documentación del fondo y el informe antes del viernes."),
    ("speaker_1", 75.02, 76.22, "De acuerdo, muchas gracias."),
]


def ev(quote: str, seg: int) -> Evidence:
    sp, start, end, _ = TURNS[seg]
    return Evidence(quote=quote, segment_id=f"s{seg:04d}", start=start, end=end, verified=True)


def build() -> dict[str, object]:
    segments = [
        Segment(id=f"s{i:04d}", speaker_id=sp, role=Role.ADVISOR if sp == "speaker_0" else Role.CLIENT,
                start=a, end=b, text=t)
        for i, (sp, a, b, t) in enumerate(TURNS)
    ]
    transcript = Transcript(audio_id="dfdf840d54fbc7fb", duration_s=76.62, segments=segments,
                            stt_provider="fixture")

    client = ClientProfile(
        client_id="CLI-DEMO-001", name="Lucía Martín (sintético)", risk_profile=3,
        horizon_years=None, liquidity_need_eur=None,
        portfolio=[
            Holding(isin="DEMO00000001", name="Fondo índice RV global (demo)", amount_eur=50_000),
            Holding(isin="DEMO00000002", name="Fondo RF corto plazo euro (demo)", amount_eur=50_000),
        ],
    )

    kids = [
        FundKID(isin="DEMO00000001", name="Fondo índice RV global (demo)", manager="Gestora Demo",
                asset_class="equity_global", sri=4, recommended_holding_years=5, ongoing_costs_pct=0.20,
                liquidity_days=3, proxy_ticker="URTH", source_url="fixture", kid_date="2026-01-01"),
        FundKID(isin="DEMO00000002", name="Fondo RF corto plazo euro (demo)", manager="Gestora Demo",
                asset_class="bond_short_eur", sri=2, recommended_holding_years=1, ongoing_costs_pct=0.15,
                liquidity_days=2, proxy_ticker="IBGS.AS", source_url="fixture", kid_date="2026-01-01"),
        FundKID(isin="DEMO00000003", name="Fondo índice RV emergente (demo)", manager="Gestora Demo",
                asset_class="equity_em", sri=4, recommended_holding_years=5, ongoing_costs_pct=0.25,
                liquidity_days=3, proxy_ticker="EEM", source_url="fixture", kid_date="2026-01-01"),
    ]

    limits = [
        RiskProfileLimits(risk_profile=1, label="Conservador", max_sri=2, max_volatility_pct=4),
        RiskProfileLimits(risk_profile=2, label="Moderado-conservador", max_sri=3, max_volatility_pct=8),
        RiskProfileLimits(risk_profile=3, label="Moderado", max_sri=4, max_volatility_pct=12),
        RiskProfileLimits(risk_profile=4, label="Dinámico", max_sri=5, max_volatility_pct=18),
        RiskProfileLimits(risk_profile=5, label="Agresivo", max_sri=7, max_volatility_pct=30),
    ]

    extraction = Extraction(
        speaker_roles={"speaker_0": Role.ADVISOR, "speaker_1": Role.CLIENT},
        circumstance_changes=[
            CircumstanceChange(id="cc1", field="horizon", description="Se jubila en tres años",
                               new_value="3 años", evidence=[ev("me jubilo en tres años", 3)]),
        ],
        stated_needs=[
            StatedNeed(id="n1", kind="horizon", description="Disponer del dinero al jubilarse",
                       horizon_years=3, evidence=[ev("me jubilo en tres años", 3)]),
            StatedNeed(id="n2", kind="liquidity", description="Entrada del piso de su hija el año que viene",
                       amount_eur=20_000, horizon_years=1,
                       evidence=[ev("Necesitaré unos veinte mil euros el año que viene", 5)]),
            StatedNeed(id="n3", kind="capital_preservation", description="No quiere sustos cerca de la jubilación",
                       evidence=[ev("Lo que no quiero es llevarme sustos", 9)]),
        ],
        recommendations=[
            Recommendation(id="r1", product_name="Fondo índice RV emergente (demo)", isin="DEMO00000003",
                           action="buy", amount_eur=30_000,
                           rationale="Mercados emergentes baratos, potencial a largo plazo; se financia vendiendo renta fija",
                           evidence=[ev("invertir treinta mil euros en un fondo indexado de renta variable emergente", 6),
                                     ev("vendiendo parte de la renta fija", 8)]),
        ],
        commitments=[
            Commitment(id="c1", who=Role.ADVISOR, description="Enviar documentación del fondo e informe",
                       due="antes del viernes",
                       evidence=[ev("Le enviaré por correo la documentación del fondo y el informe antes del viernes", 10)]),
        ],
    )

    flags = [
        Flag(id="f1", type=FlagType.HORIZON, severity=Severity.RED, recommendation_id="r1",
             title="Horizonte insuficiente",
             explanation="Horizonte recomendado KID 5 años > 3 años declarados por la clienta",
             value=3, limit=5, unit="años", evidence=[ev("me jubilo en tres años", 3)]),
        Flag(id="f2", type=FlagType.VOLATILITY, severity=Severity.RED, recommendation_id="r1",
             title="Volatilidad por encima del perfil",
             explanation="Volatilidad anual de la cartera resultante 12,2 % > 12,0 % límite del perfil 3 (Moderado) · estimación por SRI",
             value=12.2, limit=12.0, unit="%"),
        Flag(id="f3", type=FlagType.CONCENTRATION, severity=Severity.AMBER, recommendation_id="r1",
             title="Concentración elevada",
             explanation="RV emergente pasaría a 30,0 % de la cartera > 25,0 % máximo por producto",
             value=30.0, limit=25.0, unit="%"),
        Flag(id="f4", type=FlagType.SRI, severity=Severity.AMBER, recommendation_id="r1",
             title="Riesgo en el límite con preferencia por preservar capital",
             explanation="SRI del producto 4 ≤ 4 máximo del perfil 3 (Moderado)",
             value=4, limit=4, unit="SRI"),
        Flag(id="f5", type=FlagType.LIQUIDITY, severity=Severity.GREEN, recommendation_id="r1",
             title="Liquidez suficiente",
             explanation="Activos con liquidez ≤ T+3 tras la operación 100 000 € ≥ 20 000 € necesarios",
             value=100_000, limit=20_000, unit="€",
             evidence=[ev("Necesitaré unos veinte mil euros el año que viene", 5)]),
    ]

    def s(i: str, text: str, evs: list[Evidence], flags_: list[str] | None = None, kind: str = "claim") -> ReportSentence:
        return ReportSentence(id=i, text=text, kind=kind, evidence=evs, flag_ids=flags_ or [],
                              status="supported" if (evs or flags_ or kind == "boilerplate") else "no_evidence")

    report = SuitabilityReport(
        client_id=client.client_id, client_name=client.name, advisor_name="Asesor de demostración",
        meeting_date="2026-11-10", model="fixture", coverage_pct=100.0,
        sections=[
            ReportSection(key="client_situation", title="Situación de la clienta", sentences=[
                s("p1", "La clienta comunica que se jubilará en un plazo de tres años.", [ev("me jubilo en tres años", 3)]),
            ]),
            ReportSection(key="objectives_and_needs", title="Objetivos y necesidades", sentences=[
                s("p2", "Necesitará aproximadamente 20 000 € el próximo año para la entrada de la vivienda de su hija.",
                  [ev("Necesitaré unos veinte mil euros el año que viene", 5)]),
                s("p3", "Manifiesta aversión a pérdidas relevantes dada la proximidad de su jubilación.",
                  [ev("Lo que no quiero es llevarme sustos", 9)]),
            ]),
            ReportSection(key="recommendations", title="Recomendación", sentences=[
                s("p4", "El asesor recomienda invertir 30 000 € en un fondo indexado de renta variable emergente, financiado con la venta de parte de la renta fija.",
                  [ev("invertir treinta mil euros en un fondo indexado de renta variable emergente", 6),
                   ev("vendiendo parte de la renta fija", 8)]),
            ]),
            ReportSection(key="suitability_assessment", title="Evaluación de idoneidad", sentences=[
                s("p5", "El horizonte mínimo recomendado del producto (5 años) supera el horizonte declarado (3 años).",
                  [ev("me jubilo en tres años", 3)], ["f1"]),
                s("p6", "La volatilidad estimada de la cartera resultante (12,2 %) excede el límite del perfil Moderado (12,0 %).",
                  [], ["f2"], kind="computed"),
            ]),
            ReportSection(key="risks_and_warnings", title="Riesgos y advertencias", sentences=[
                s("p7", "Con la información disponible, la recomendación presenta incoherencias con el perfil que deben resolverse antes de ejecutarse.",
                  [], ["f1", "f2", "f3"], kind="computed"),
            ]),
            ReportSection(key="commitments", title="Compromisos", sentences=[
                s("p8", "El asesor se compromete a remitir la documentación del fondo y este informe antes del viernes.",
                  [ev("Le enviaré por correo la documentación del fondo y el informe antes del viernes", 10)]),
            ]),
        ],
    )

    ok, breach, none = ConductStatus.OK, ConductStatus.BREACH, ConductStatus.NO_EVIDENCE
    conduct = ConductCheck(model="fixture", items=[
        ConductItem(code="recording_notice", title="Aviso de grabación", rule="MiFID II art. 16.7; Reg. Del. 2017/565 art. 76",
                    status=ok, explanation="El asesor informa de la grabación y la clienta lo acepta.",
                    evidence=[ev("esta reunión se graba con su consentimiento", 0), ev("Sí, sin problema.", 1)]),
        ConductItem(code="circumstances_updated", title="Se actualiza la situación del cliente", rule="Reg. Del. 2017/565 art. 54",
                    status=ok, explanation="El asesor pregunta por gastos importantes antes de recomendar.",
                    evidence=[ev("¿Hay algún gasto importante antes de esa fecha?", 4)]),
        ConductItem(code="return_promise", title="Sin promesas de rentabilidad", rule="MiFID II art. 24.3",
                    status=breach, explanation="Se asegura que la clienta no perderá dinero en un fondo de renta variable.",
                    evidence=[ev("con este no va a perder dinero", 8)]),
        ConductItem(code="risks_explained", title="Riesgos explicados", rule="MiFID II art. 24.4",
                    status=breach, explanation="La clienta dice no entender el producto y no se le explican sus riesgos.",
                    evidence=[ev("no entiendo mucho de esto", 7), ev("Es un fondo con buen potencial a largo plazo", 8)]),
        ConductItem(code="costs_disclosed", title="Costes informados", rule="MiFID II art. 24.4.c; Reg. Del. 2017/565 art. 50",
                    status=none, explanation="No se mencionan los costes del fondo."),
        ConductItem(code="commercial_pressure", title="Sin presión comercial", rule="MiFID II art. 24.1",
                    status=ok, explanation="No se aprecia prisa ni presión para decidir."),
        ConductItem(code="conflicts_of_interest", title="Conflictos de interés e incentivos", rule="MiFID II arts. 23 y 24.9",
                    status=none, explanation="No se habla de incentivos ni de conflictos de interés."),
    ])

    summary = ClientSummary(title="Resumen de tu reunión", model="fixture", points=[
        SummaryPoint(text="Nos contaste que te jubilas dentro de tres años.", evidence=[ev("me jubilo en tres años", 3)]),
        SummaryPoint(text="Necesitarás unos 20 000 € el año que viene para la entrada del piso de tu hija.",
                     evidence=[ev("Necesitaré unos veinte mil euros el año que viene", 5)]),
        SummaryPoint(text="Tu asesor te propuso invertir 30 000 € en un fondo de renta variable de países emergentes, "
                          "vendiendo parte de tu renta fija.",
                     evidence=[ev("invertir treinta mil euros en un fondo indexado de renta variable emergente", 6)]),
    ], next_steps=[
        SummaryPoint(text="Recibirás por correo la documentación del fondo y el informe antes del viernes.",
                     evidence=[ev("Le enviaré por correo la documentación del fondo y el informe antes del viernes", 10)]),
    ])

    result = AnalysisResult(
        analysis_id="AN-DEMO-0001", client=client, transcript=transcript, extraction=extraction,
        flags=flags, report=report, conduct=conduct, client_summary=summary,
        timings=[StageTiming(stage=st, seconds=0.0, fake=True)
                 for st in ("stt", "extract", "validate", "check", "conduct", "summary", "report")],
    )
    return {
        "transcript": transcript, "client": client, "kids": kids, "risk_limits": limits,
        "extraction": extraction, "flags": flags, "report": report, "conduct": conduct,
        "client_summary": summary, "analysis_result": result,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, obj in build().items():
        if isinstance(obj, list):
            data = [o.model_dump(mode="json") for o in obj]
        else:
            data = obj.model_dump(mode="json")
        (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fixtures written to {OUT}")


if __name__ == "__main__":
    main()
