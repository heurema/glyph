"""Tests for scene schema validation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.errors import SchemaError
from pipeline.schema import validate_scene

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


class TestValidScenes:
    def test_minimal(self):
        scene = validate_scene(_load("minimal.json"))
        assert scene.version == "1.0"
        assert len(scene.beats) == 1
        assert scene.beats[0].type == "shell"

    def test_full_demo(self):
        scene = validate_scene(_load("full_demo.json"))
        assert len(scene.beats) == 5
        assert scene.config.cols == 100
        assert scene.config.seed == 42

    def test_defaults_applied(self):
        scene = validate_scene({"version": "1.0", "beats": []})
        assert scene.config.cols == 100
        assert scene.config.rows == 30
        assert scene.config.shell_prompt == "$ "
        assert scene.config.theme == "default"


class TestInvalidScenes:
    def test_missing_version(self):
        with pytest.raises(SchemaError, match="version"):
            validate_scene({"beats": []})

    def test_unknown_beat_type(self):
        with pytest.raises(SchemaError):
            validate_scene(_load("invalid_beat.json"))

    def test_missing_required_field(self):
        with pytest.raises(SchemaError):
            validate_scene({
                "version": "1.0",
                "beats": [{"type": "shell"}]
            })


class TestBoundaries:
    def test_exactly_50_beats(self):
        data = {
            "version": "1.0",
            "beats": [
                {"type": "shell", "command": f"echo {i}", "output": [str(i)], "pause_after": 0.1}
                for i in range(50)
            ],
        }
        scene = validate_scene(data)
        assert len(scene.beats) == 50

    def test_51_beats_rejected(self):
        data = {
            "version": "1.0",
            "beats": [
                {"type": "shell", "command": f"echo {i}", "output": [str(i)], "pause_after": 0.1}
                for i in range(51)
            ],
        }
        with pytest.raises(SchemaError, match="50"):
            validate_scene(data)

    def test_exactly_120s(self):
        data = {
            "version": "1.0",
            "beats": [
                {"type": "pause", "duration": 60.0},
                {"type": "pause", "duration": 60.0},
            ],
        }
        scene = validate_scene(data)
        assert len(scene.beats) == 2

    def test_121s_rejected(self):
        data = {
            "version": "1.0",
            "beats": [
                {"type": "pause", "duration": 60.0},
                {"type": "pause", "duration": 61.0},
            ],
        }
        with pytest.raises(SchemaError, match="120"):
            validate_scene(data)

    def test_empty_beats_allowed(self):
        scene = validate_scene({"version": "1.0", "beats": []})
        assert len(scene.beats) == 0
