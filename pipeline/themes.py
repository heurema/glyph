# pipeline/themes.py
"""Theme loading and configuration."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import BaseModel

log = logging.getLogger(__name__)

RESOURCES_DIR = Path(__file__).parent.parent / "resources" / "themes"


class ThemeConfig(BaseModel):
    """ANSI theme configuration."""

    name: str = "default"
    prompt_color: str = "\x1b[1m"
    output_color: str = "\x1b[0m"
    comment_color: str = "\x1b[90m"
    highlight_color: str = "\x1b[32m"
    agg_theme: str = "monokai"
    agg_font_size: int = 16


def _load_from_path(path: Path) -> ThemeConfig | None:
    """Try loading theme from a JSON file path."""
    try:
        data = json.loads(path.read_text())
        return ThemeConfig.model_validate(data)
    except Exception as e:
        log.warning("Failed to load theme from %s: %s", path, e)
        return None


def load_theme(name_or_path: str) -> ThemeConfig:
    """Load a theme by name (from resources/) or file path.

    Falls back to default theme if not found or invalid.
    """
    # Try as file path first
    path = Path(name_or_path)
    if path.is_file():
        result = _load_from_path(path)
        if result:
            return result

    # Try as named theme in resources
    resource_path = RESOURCES_DIR / f"{name_or_path}.json"
    if resource_path.is_file():
        result = _load_from_path(resource_path)
        if result:
            return result

    # Fallback to default
    if name_or_path != "default":
        log.warning("Theme '%s' not found, falling back to default", name_or_path)
        default_path = RESOURCES_DIR / "default.json"
        if default_path.is_file():
            result = _load_from_path(default_path)
            if result:
                return result

    return ThemeConfig()
