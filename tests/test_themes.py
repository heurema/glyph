"""Tests for theme loading."""
from __future__ import annotations

import json
from pathlib import Path

from pipeline.themes import load_theme


class TestLoadTheme:
    def test_load_default(self):
        theme = load_theme("default")
        assert theme.name == "default"
        assert theme.agg_theme == "monokai"
        assert theme.agg_font_size == 16

    def test_load_amber(self):
        theme = load_theme("amber")
        assert theme.name == "amber"
        assert "\x1b[33" in theme.prompt_color

    def test_unknown_falls_back_to_default(self):
        theme = load_theme("nonexistent")
        assert theme.name == "default"

    def test_load_from_path(self, tmp_path: Path):
        custom = {
            "name": "custom",
            "prompt_color": "\x1b[35m",
            "output_color": "\x1b[0m",
            "comment_color": "\x1b[90m",
            "highlight_color": "\x1b[36m",
            "agg_theme": "dracula",
            "agg_font_size": 14,
        }
        p = tmp_path / "custom.json"
        p.write_text(json.dumps(custom))
        theme = load_theme(str(p))
        assert theme.name == "custom"
        assert theme.agg_font_size == 14

    def test_invalid_json_falls_back(self, tmp_path: Path):
        p = tmp_path / "broken.json"
        p.write_text("{invalid json")
        theme = load_theme(str(p))
        assert theme.name == "default"

    def test_missing_keys_use_defaults(self, tmp_path: Path):
        p = tmp_path / "partial.json"
        p.write_text(json.dumps({"name": "partial"}))
        theme = load_theme(str(p))
        assert theme.name == "partial"
        assert theme.agg_font_size == 16
