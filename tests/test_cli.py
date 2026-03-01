"""Tests for CLI entry point."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pipeline", *args],
        capture_output=True,
        text=True,
        cwd=cwd or Path(__file__).parent.parent,
    )


class TestCLI:
    def test_no_args_shows_usage(self):
        result = _run_cli()
        assert result.returncode != 0
        assert "usage" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_valid_scene(self, tmp_path: Path):
        scene = {"version": "1.0", "beats": [{"type": "comment", "text": "# hello"}]}
        scene_path = tmp_path / "scene.json"
        scene_path.write_text(json.dumps(scene))

        result = _run_cli(str(scene_path), "--output", str(tmp_path))
        assert result.returncode == 0
        assert (tmp_path / "scene.cast").exists()

    def test_invalid_scene_exit_1(self, tmp_path: Path):
        scene_path = tmp_path / "bad.json"
        scene_path.write_text(json.dumps({"beats": []}))

        result = _run_cli(str(scene_path), "--output", str(tmp_path))
        assert result.returncode == 1

    def test_pii_scene_exit_2(self, tmp_path: Path):
        scene = {
            "version": "1.0",
            "beats": [
                {"type": "shell", "command": "cat file.txt", "output": ["/Users/john/secret"]}
            ],
        }
        scene_path = tmp_path / "pii.json"
        scene_path.write_text(json.dumps(scene))

        result = _run_cli(str(scene_path), "--output", str(tmp_path))
        assert result.returncode == 2

    def test_nonexistent_file_exit_1(self, tmp_path: Path):
        result = _run_cli(str(tmp_path / "nope.json"), "--output", str(tmp_path))
        assert result.returncode == 1
