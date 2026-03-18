"""PII and secrets audit for rendered asciicast events."""
from __future__ import annotations

from dataclasses import dataclass

from .renderer import Event

PII_PATTERNS: list[str] = [
    "/Users/",
    "/home/",
    "~",
    "API_KEY",
    "Bearer ",
    "sk-",
    "ANTHROPIC_",
    "TAVILY_",
    "@gmail",
    "@yahoo",
    "password",
    "secret",
    "credential",
]


@dataclass
class Finding:
    """A single PII finding."""

    pattern: str
    event_index: int
    snippet: str


def _is_exempt(data: str, pattern: str, pos: int) -> bool:
    """Check if a match is a false positive."""
    if pattern == "~":
        prefix = data[:pos]
        if "://" in prefix:
            return True
        if pos + 1 < len(data) and data[pos + 1] != "/":
            return True
    return False


def audit(events: list[Event], allow: list[str] | None = None) -> list[Finding]:
    """Scan events for PII/secret patterns. Returns list of findings.

    Args:
        allow: patterns to suppress (e.g. ["password", "secret"] for CLI demos).
    """
    allow_lower = {p.lower() for p in (allow or [])}
    findings: list[Finding] = []
    for idx, event in enumerate(events):
        data_lower = event.data.lower()
        for pattern in PII_PATTERNS:
            if pattern.lower() in allow_lower:
                continue
            pattern_lower = pattern.lower()
            pos = data_lower.find(pattern_lower)
            if pos == -1:
                continue
            if _is_exempt(event.data, pattern, pos):
                continue
            snippet = event.data.replace("\r\n", "\\n").replace("\n", "\\n")[:80]
            findings.append(Finding(
                pattern=pattern,
                event_index=idx,
                snippet=snippet,
            ))
    return findings
