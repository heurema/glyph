"""Tests for main orchestrator."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from pipeline.main import run

AGG_AVAILABLE = shutil.which("agg") is not None


def _write_scene(path: Path, scene: dict) -> Path:
    p = path / "scene.json"
    p.write_text(json.dumps(scene))
    return p


class TestRunSuccess:
    @pytest.mark.skipif(not AGG_AVAILABLE, reason="agg not installed")
    def test_minimal_scene_produces_gif(self, tmp_path: Path):
        scene_path = _write_scene(tmp_path, {
            "version": "1.0",
            "beats": [{"type": "shell", "command": "echo hi", "output": ["hi"]}],
        })
        result = run(scene_path, tmp_path)
        assert result.success
        assert result.gif_path is not None
        assert result.gif_path.exists()
        assert result.cast_path is not None
        assert result.cast_path.exists()
        assert result.frame_count > 0
        assert result.duration > 0.0

    def test_cast_only_without_agg(self, tmp_path: Path):
        scene_path = _write_scene(tmp_path, {
            "version": "1.0",
            "beats": [{"type": "shell", "command": "echo hi", "output": ["hi"]}],
        })
        with patch("pipeline.main._try_build_gif", return_value=None):
            result = run(scene_path, tmp_path)
        assert result.success
        assert result.cast_path is not None
        assert result.cast_path.exists()
        assert result.gif_path is None


class TestRunErrors:
    def test_invalid_scene_returns_error(self, tmp_path: Path):
        scene_path = _write_scene(tmp_path, {"beats": []})
        result = run(scene_path, tmp_path)
        assert not result.success
        assert len(result.errors) > 0

    def test_pii_blocks_output(self, tmp_path: Path):
        scene_path = _write_scene(tmp_path, {
            "version": "1.0",
            "beats": [
                {"type": "shell", "command": "cat /Users/john/.ssh/key", "output": ["secret"]}
            ],
        })
        result = run(scene_path, tmp_path)
        assert not result.success
        assert len(result.pii_findings) > 0
        assert result.cast_path is None
        assert result.gif_path is None

    def test_nonexistent_scene_file(self, tmp_path: Path):
        result = run(tmp_path / "nope.json", tmp_path)
        assert not result.success


class TestRunResult:
    def test_result_fields(self, tmp_path: Path):
        scene_path = _write_scene(tmp_path, {
            "version": "1.0",
            "beats": [{"type": "comment", "text": "# clean"}],
        })
        with patch("pipeline.main._try_build_gif", return_value=None):
            result = run(scene_path, tmp_path)
        assert isinstance(result.success, bool)
        assert isinstance(result.duration, float)
        assert isinstance(result.frame_count, int)
        assert isinstance(result.pii_findings, list)
        assert isinstance(result.errors, list)
