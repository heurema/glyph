"""Shared fixtures for glyph tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def minimal_scene() -> dict:
    return json.loads((FIXTURES_DIR / "minimal.json").read_text())


@pytest.fixture
def full_scene() -> dict:
    return json.loads((FIXTURES_DIR / "full_demo.json").read_text())
