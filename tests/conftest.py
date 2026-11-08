"""Shared pytest fixtures. Owner: D."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import fakes  # noqa: E402
from app.config import STAGES, get_settings  # noqa: E402


@pytest.fixture
def fake_settings():
    """Settings with every stage faked (no API calls)."""
    return get_settings(fake_stages=frozenset(STAGES))


@pytest.fixture
def demo_transcript():
    return fakes.transcript()


@pytest.fixture
def demo_client():
    return fakes.client()


@pytest.fixture
def demo_extraction():
    return fakes.extraction()


@pytest.fixture
def demo_flags():
    return fakes.flags()


@pytest.fixture
def demo_result():
    return fakes.analysis_result()
