"""Pipeline orchestrator: validate -> render -> audit -> write -> gif."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from .agg import build_gif
from .errors import AggError, GlyphError, SchemaError
from .pii import Finding, audit
from .renderer import Event, render
from .schema import validate_scene
from .themes import ThemeConfig, load_theme

log = logging.getLogger(__name__)


@dataclass
class RunResult:
    """Result of a pipeline run."""

    success: bool = False
    gif_path: Path | None = None
    cast_path: Path | None = None
    duration: float = 0.0
    frame_count: int = 0
    pii_findings: list[Finding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _write_cast(events: list[Event], path: Path, cols: int, rows: int, title: str) -> None:
    """Write asciicast v2 file."""
    header = {
        "version": 2,
        "width": cols,
        "height": rows,
        "title": title,
        "env": {"SHELL": "/bin/zsh", "TERM": "xterm-256color"},
    }
    with path.open("w") as f:
        f.write(json.dumps(header) + "\n")
        for event in events:
            f.write(json.dumps([event.time, event.type, event.data]) + "\n")


def _try_build_gif(cast_path: Path, gif_path: Path, theme: ThemeConfig) -> Path | None:
    """Attempt GIF conversion. Returns None if agg unavailable."""
    try:
        return build_gif(cast_path, gif_path, theme)
    except AggError as e:
        log.warning("GIF conversion skipped: %s", e)
        return None


def run(scene_path: Path, output_dir: Path) -> RunResult:
    """Run the full pipeline: validate -> render -> audit -> write -> gif.

    Returns RunResult with success status and artifacts.
    """
    result = RunResult()

    # 1. Read scene file
    try:
        data = json.loads(scene_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        result.errors.append(f"Failed to read scene: {e}")
        return result

    # 2. Validate
    try:
        scene = validate_scene(data)
    except SchemaError as e:
        result.errors.append(f"Schema validation failed: {e}")
        return result

    # 3. Load theme
    theme = load_theme(scene.config.theme)

    # 4. Render
    try:
        events = render(scene, theme)
    except GlyphError as e:
        result.errors.append(f"Render failed: {e}")
        return result

    result.frame_count = len(events)
    result.duration = events[-1].time if events else 0.0

    # 5. PII audit — BEFORE writing any files
    findings = audit(events)
    result.pii_findings = findings
    if findings:
        patterns = ", ".join(f.pattern for f in findings)
        result.errors.append(f"PII detected ({len(findings)} findings): {patterns}")
        return result

    # 6. Write .cast
    output_dir.mkdir(parents=True, exist_ok=True)
    cast_path = output_dir / f"{scene_path.stem}.cast"
    _write_cast(events, cast_path, scene.config.cols, scene.config.rows, scene.config.title)
    result.cast_path = cast_path

    # 7. Build GIF
    gif_path = output_dir / f"{scene_path.stem}.gif"
    result.gif_path = _try_build_gif(cast_path, gif_path, theme)

    result.success = True
    return result
