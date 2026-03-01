"""Tests for glyph error hierarchy."""
from pipeline.errors import AggError, GlyphError, PIIError, RenderError, SchemaError


def test_hierarchy():
    assert issubclass(SchemaError, GlyphError)
    assert issubclass(PIIError, GlyphError)
    assert issubclass(RenderError, GlyphError)
    assert issubclass(AggError, GlyphError)


def test_pii_error_findings():
    findings = [{"pattern": "/Users/", "position": 42}]
    err = PIIError(findings)
    assert err.findings == findings
    assert "1 finding" in str(err)


def test_schema_error_message():
    err = SchemaError("missing field: version")
    assert "missing field: version" in str(err)
