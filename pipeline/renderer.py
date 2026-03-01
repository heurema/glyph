# pipeline/renderer.py
"""Asciicast v2 renderer — converts Scene to cast events."""
from __future__ import annotations

import random
from dataclasses import dataclass

from .errors import RenderError
from .schema import AppBeat, ClearBeat, CommentBeat, PauseBeat, Scene, ShellBeat
from .themes import ThemeConfig

CHAR_DELAY = 0.065
CHAR_JITTER = 0.025
LINE_PAUSE = 0.4
OUTPUT_LINE_DELAY = 0.02
RESET = "\x1b[0m"


@dataclass
class Event:
    """A single asciicast v2 event."""

    time: float
    type: str  # "o" for output
    data: str


class CastWriter:
    """Accumulates timed output events."""

    def __init__(self, seed: int | None = None) -> None:
        self.time = 0.0
        self.events: list[Event] = []
        self._rng = random.Random(seed)

    def advance(self, dt: float) -> None:
        self.time += dt

    def output(self, text: str) -> None:
        self.events.append(Event(round(self.time, 6), "o", text))

    def type_text(self, text: str) -> None:
        for ch in text:
            self.output(ch)
            jitter = self._rng.uniform(-CHAR_JITTER, CHAR_JITTER)
            self.advance(CHAR_DELAY + jitter)

    def newline(self) -> None:
        self.output("\r\n")
        self.advance(LINE_PAUSE)

    def print_lines(self, lines: list[str]) -> None:
        for line in lines:
            self.output(line + "\r\n")
            self.advance(OUTPUT_LINE_DELAY)


def _emit_shell(w: CastWriter, beat: ShellBeat, theme: ThemeConfig) -> None:
    w.output(f"{theme.prompt_color}$ {RESET}")
    w.type_text(beat.command)
    w.newline()
    if beat.output:
        w.print_lines([f"{theme.output_color}{line}{RESET}" for line in beat.output])
    w.advance(beat.pause_after)


def _emit_app(w: CastWriter, beat: AppBeat, theme: ThemeConfig) -> None:
    w.output(f"{theme.highlight_color}>{RESET} ")
    w.type_text(beat.command)
    w.newline()
    if beat.output:
        w.print_lines([f"{theme.output_color}{line}{RESET}" for line in beat.output])
    w.advance(beat.pause_after)


def _emit_clear(w: CastWriter, _beat: ClearBeat, _theme: ThemeConfig) -> None:
    w.output("\x1b[2J\x1b[H")
    w.advance(0.3)


def _emit_comment(w: CastWriter, beat: CommentBeat, theme: ThemeConfig) -> None:
    w.output(f"{theme.comment_color}{beat.text}{RESET}\r\n")
    w.advance(0.5)


def _emit_pause(w: CastWriter, beat: PauseBeat, _theme: ThemeConfig) -> None:
    w.advance(beat.duration)


_EMITTERS = {
    "shell": _emit_shell,
    "app": _emit_app,
    "clear": _emit_clear,
    "comment": _emit_comment,
    "pause": _emit_pause,
}


def render(scene: Scene, theme: ThemeConfig) -> list[Event]:
    """Render a Scene into asciicast v2 events."""
    if not scene.beats:
        return []

    try:
        w = CastWriter(seed=scene.config.seed)
        for beat in scene.beats:
            emitter = _EMITTERS.get(beat.type)
            if emitter is None:
                raise RenderError(f"Unknown beat type: {beat.type}")
            emitter(w, beat, theme)
        return w.events
    except RenderError:
        raise
    except Exception as e:
        raise RenderError(str(e)) from e
