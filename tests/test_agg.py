"""Tests for agg GIF conversion."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from pipeline.agg import build_gif, ensure_agg
from pipeline.errors import AggError

AGG_AVAILABLE = shutil.which("agg") is not None


class TestEnsureAgg:
    def test_finds_agg_on_path(self):
        if not AGG_AVAILABLE:
            pytest.skip("agg not installed")
        path = ensure_agg()
        assert Path(path).name == "agg"

    def test_uses_agg_path_env(self, tmp_path: Path):
        fake_agg = tmp_path / "agg"
        fake_agg.write_text("#!/bin/sh\nexit 0")
        fake_agg.chmod(0o755)
        with patch.dict("os.environ", {"AGG_PATH": str(fake_agg)}):
            path = ensure_agg()
            assert path == str(fake_agg)

    def test_raises_when_not_found(self):
        with patch("shutil.which", return_value=None), \
             patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AggError, match="not found"):
                ensure_agg()


class TestBuildGif:
    @pytest.mark.skipif(not AGG_AVAILABLE, reason="agg not installed")
    def test_creates_gif(self, tmp_path: Path):
        cast_path = tmp_path / "test.cast"
        header = {"version": 2, "width": 80, "height": 24}
        events = [[0.0, "o", "hello\r\n"], [1.0, "o", "world\r\n"]]
        with cast_path.open("w") as f:
            f.write(json.dumps(header) + "\n")
            for ev in events:
                f.write(json.dumps(ev) + "\n")

        gif_path = tmp_path / "test.gif"
        result = build_gif(cast_path, gif_path)
        assert result.exists()
        assert result.stat().st_size > 0

    def test_raises_on_missing_cast(self, tmp_path: Path):
        if not AGG_AVAILABLE:
            pytest.skip("agg not installed")
        with pytest.raises(AggError):
            build_gif(tmp_path / "nonexistent.cast", tmp_path / "out.gif")
