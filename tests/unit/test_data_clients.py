"""Synthetic clients and risk limits (C-4): every holding is a real ISIN of the KID catalogue."""

from __future__ import annotations

from app.data.loaders import list_clients, load_client, load_kids, load_risk_limits


def test_risk_limits_cover_profiles_1_to_5():
    limits = load_risk_limits()
    assert sorted(limits) == [1, 2, 3, 4, 5]
    assert [limits[p].max_sri for p in range(1, 6)] == sorted(limits[p].max_sri for p in range(1, 6))


def test_clients_are_synthetic_and_use_catalogue_isins():
    kids = load_kids()
    clients = list_clients()
    assert len(clients) >= 4 and any(c.client_id == "CLI-DEMO-001" for c in clients)
    for c in clients:
        assert c.synthetic and "(sintético)" in c.name
        for h in c.portfolio:
            assert h.isin in kids, f"{c.client_id}: {h.isin} no está en kids.json"


def test_demo_client_matches_the_clip():
    c = load_client("CLI-DEMO-001")
    assert c.risk_profile == 3 and sum(h.amount_eur for h in c.portfolio) == 100_000


def test_eval_clients_copied_to_app_are_in_sync():
    """app/data/clients/CLI-EVAL-*.json must equal tests/eval/meetings/*/client.json (owned by D)."""
    import json

    from app.data.loaders import DATA

    root = DATA.parents[1] / "tests" / "eval" / "meetings"
    for f in sorted(root.glob("*/client.json")):
        src = json.loads(f.read_text(encoding="utf-8"))
        copy = DATA / "clients" / f"{src['client_id']}.json"
        assert copy.exists() and json.loads(copy.read_text(encoding="utf-8")) == src, f"{copy.name} desfasado"
