"""Quantitative checker (C-04) on the demo fixture, with the SRI volatility approximation."""

from __future__ import annotations

from app import fakes
from app.engine.checker import check


def test_demo_story_flags(demo_extraction, demo_client):
    flags = check(demo_extraction, demo_client, kids=fakes.kids(), limits=fakes.risk_limits())
    by_type = {f.type.value: f for f in flags}
    assert set(by_type) == {"sri", "horizon", "concentration", "liquidity", "volatility"}
    assert by_type["horizon"].severity.value == "red" and by_type["horizon"].evidence
    assert by_type["concentration"].severity.value == "amber" and by_type["concentration"].value == 30.0
    assert by_type["sri"].severity.value == "amber"  # SRI = máximo y la clienta no quiere sustos (CONTRACT)
    assert by_type["liquidity"].severity.value == "green"
    assert by_type["volatility"].severity.value == "red"
    assert "%" in by_type["volatility"].explanation and "," in by_type["volatility"].explanation
    assert [f.id for f in flags] == [f"f{i}" for i in range(1, 6)]


def test_no_recommendations_no_flags(demo_client):
    from app.schemas import Extraction

    assert check(Extraction(), demo_client, kids=fakes.kids(), limits=fakes.risk_limits()) == []


def test_years_formatting():
    from app.engine.checker import years

    assert years(5) == "5 años" and years(1) == "1 año" and years(1.5) == "1,5 años"
    assert years(0.08) == "1 mes" and years(0.5) == "6 meses"


def test_flags_ordered_by_severity_then_type():
    from app.engine.checker import order_flags
    from app.schemas import Flag, FlagType, Severity

    def f(i, t, s):
        return Flag(id=i, type=t, severity=s, title="x", explanation="x")

    out = order_flags([f("f1", FlagType.SRI, Severity.AMBER), f("f2", FlagType.HORIZON, Severity.RED),
                       f("f3", FlagType.LIQUIDITY, Severity.GREEN), f("f4", FlagType.VOLATILITY, Severity.RED),
                       f("f5", FlagType.CONCENTRATION, Severity.AMBER)])
    assert [(x.id, x.type) for x in out] == [("f1", FlagType.HORIZON), ("f2", FlagType.VOLATILITY),
                                              ("f3", FlagType.CONCENTRATION), ("f4", FlagType.SRI),
                                              ("f5", FlagType.LIQUIDITY)]
