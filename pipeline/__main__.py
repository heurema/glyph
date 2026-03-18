"""CLI entry point: python -m pipeline <scene.json> [--output dir] [--theme name]."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .main import run


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="glyph-pipeline",
        description="Generate terminal demo GIF from scene JSON.",
    )
    parser.add_argument("scene", type=Path, help="Path to scene JSON file")
    parser.add_argument("--output", "-o", type=Path, default=Path("."), help="Output directory")
    parser.add_argument("--theme", "-t", type=str, default=None, help="Theme name or path")

    args = parser.parse_args()

    result = run(args.scene, args.output, theme_override=args.theme)

    if result.pii_findings:
        print(f"ERROR: PII detected ({len(result.pii_findings)} findings):", file=sys.stderr)
        for f in result.pii_findings:
            print(f"  [{f.pattern}] {f.snippet}", file=sys.stderr)
        return 2

    if not result.success:
        for err in result.errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    # Success output
    print(f"Cast: {result.cast_path} ({result.frame_count} frames, {result.duration:.1f}s)")
    if result.gif_path:
        size_kb = result.gif_path.stat().st_size / 1024
        print(f"GIF:  {result.gif_path} ({size_kb:.0f} KB)")
    else:
        print("GIF:  skipped (agg not available)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
