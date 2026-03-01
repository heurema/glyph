"""agg binary detection and GIF conversion."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .errors import AggError
from .themes import ThemeConfig


def ensure_agg() -> str:
    """Find the agg binary. Checks AGG_PATH env, then PATH.

    Raises AggError if not found.
    """
    env_path = os.environ.get("AGG_PATH")
    if env_path and Path(env_path).is_file():
        return env_path

    which = shutil.which("agg")
    if which:
        return which

    raise AggError(
        "agg not found. Install: brew install agg (macOS) "
        "or cargo install --git https://github.com/asciinema/agg"
    )


def build_gif(
    cast_path: Path,
    gif_path: Path,
    theme: ThemeConfig | None = None,
) -> Path:
    """Convert .cast file to .gif using agg.

    Returns the path to the generated GIF.
    Raises AggError on failure.
    """
    agg_bin = ensure_agg()

    if not cast_path.is_file():
        raise AggError(f"Cast file not found: {cast_path}")

    cmd = [agg_bin, str(cast_path), str(gif_path)]
    if theme:
        cmd.extend(["--theme", theme.agg_theme])
        cmd.extend(["--font-size", str(theme.agg_font_size)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise AggError(f"agg failed (exit {result.returncode}): {result.stderr}")
    except subprocess.TimeoutExpired as e:
        raise AggError("agg timed out after 60s") from e
    except FileNotFoundError as e:
        raise AggError(f"agg binary not executable: {agg_bin}") from e

    if not gif_path.is_file():
        raise AggError(f"agg did not produce output: {gif_path}")

    return gif_path
