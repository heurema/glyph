"""Domain exceptions for glyph pipeline."""
from __future__ import annotations


class GlyphError(Exception):
    """Base exception for all glyph errors."""


class SchemaError(GlyphError):
    """Invalid scene JSON or constraint violations."""


class PIIError(GlyphError):
    """PII detected in rendered output."""

    def __init__(self, findings: list[dict[str, object]]) -> None:
        self.findings = findings
        super().__init__(f"PII detected: {len(findings)} finding(s)")


class RenderError(GlyphError):
    """Asciicast generation failure."""


class AggError(GlyphError):
    """agg binary missing or conversion failure."""
