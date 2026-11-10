"""Ownership rules behave as CLAUDE.md §2 says. Owner: D."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from ownership import verdict  # noqa: E402


def test_each_role_owns_its_area():
    assert verdict("A", "app/ui/streamlit_app.py")[0]
    assert verdict("B", "app/engine/citations.py")[0]
    assert verdict("C", "app/engine/checker.py")[0]
    assert verdict("D", "tests/integration/test_contract.py")[0]


def test_cross_role_edits_are_blocked():
    ok, reason = verdict("A", "app/engine/checker.py")
    assert not ok and "rol C" in reason
    assert not verdict("C", "app/engine/report.py")[0]


def test_frozen_and_shared():
    assert not verdict("B", "app/schemas.py")[0]
    assert verdict("B", "docs/TASKS.md")[0]
    assert verdict("A", ".env")[0]
