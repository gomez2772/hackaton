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
