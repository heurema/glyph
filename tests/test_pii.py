"""Tests for PII audit."""
from __future__ import annotations

from pipeline.pii import audit
from pipeline.renderer import Event


def _events(texts: list[str]) -> list[Event]:
    return [Event(time=float(i), type="o", data=t) for i, t in enumerate(texts)]


class TestDetection:
    def test_detects_home_path(self):
        findings = audit(_events(["/Users/john/file.txt"]))
        assert len(findings) >= 1
        assert any("/Users/" in f.pattern for f in findings)

    def test_detects_linux_home(self):
        findings = audit(_events(["/home/user/data"]))
        assert len(findings) >= 1

    def test_detects_api_key(self):
        findings = audit(_events(["export API_KEY=abc123"]))
        assert len(findings) >= 1

    def test_detects_bearer_token(self):
        findings = audit(_events(["Authorization: Bearer eyJhbGci..."]))
        assert len(findings) >= 1

    def test_detects_sk_prefix(self):
        findings = audit(_events(["sk-proj-abc123def456"]))
        assert len(findings) >= 1

    def test_detects_anthropic_env(self):
        findings = audit(_events(["ANTHROPIC_API_KEY=..."]))
        assert len(findings) >= 1

    def test_detects_tavily_env(self):
        findings = audit(_events(["TAVILY_API_KEY=..."]))
        assert len(findings) >= 1

    def test_detects_email(self):
        findings = audit(_events(["user@gmail.com"]))
        assert len(findings) >= 1

    def test_detects_password(self):
        findings = audit(_events(["password=secret123"]))
        assert len(findings) >= 1

    def test_detects_credential(self):
        findings = audit(_events(["loading credentials..."]))
        assert len(findings) >= 1


class TestCleanPass:
    def test_clean_events_no_findings(self):
        findings = audit(_events(["echo hello", "npm install", "$ ls"]))
        assert findings == []

    def test_normal_urls_clean(self):
        findings = audit(_events(["https://github.com/heurema/glyph"]))
        assert findings == []


class TestFalsePositives:
    def test_uuid_not_flagged(self):
        findings = audit(_events(["id: 550e8400-e29b-41d4-a716-446655440000"]))
        assert findings == []

    def test_semver_not_flagged(self):
        findings = audit(_events(["v2.1.63"]))
        assert findings == []


class TestFindingStructure:
    def test_finding_has_fields(self):
        findings = audit(_events(["/Users/john/secret"]))
        assert len(findings) >= 1
        f = findings[0]
        assert isinstance(f.pattern, str)
        assert isinstance(f.event_index, int)
        assert isinstance(f.snippet, str)
