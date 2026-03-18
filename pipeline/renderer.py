# pipeline/renderer.py
"""Asciicast v2 renderer — converts Scene to cast events."""
from __future__ import annotations

import random
from dataclasses import dataclass

from .errors import RenderError
from .schema import AppBeat, ClearBeat, ColoredLine, CommentBeat, OutputLine, PauseBeat, Scene, ShellBeat
from .themes import ThemeConfig

CHAR_DELAY = 0.065
CHAR_JITTER = 0.025
LINE_PAUSE = 0.4
OUTPUT_LINE_DELAY = 0.02
RESET = "\x1b[0m"

ANSI_COLORS: dict[str, str] = {
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "magenta": "\x1b[35m",
    "cyan": "\x1b[36m",
    "white": "\x1b[37m",
    "dim": "\x1b[2m",
    "bold": "\x1b[1m",
    "bold_red": "\x1b[1;31m",
    "bold_green": "\x1b[1;32m",
    "bold_yellow": "\x1b[1;33m",
}


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

    def type_text(self, text: str, char_delay: float | None = None) -> None:
        delay = char_delay or CHAR_DELAY
        for ch in text:
            self.output(ch)
            jitter = self._rng.uniform(-CHAR_JITTER, CHAR_JITTER)
            self.advance(delay + jitter)

    def newline(self) -> None:
        self.output("\r\n")
        self.advance(LINE_PAUSE)

    def print_lines(self, lines: list[str]) -> None:
        for line in lines:
            self.output(line + "\r\n")
            self.advance(OUTPUT_LINE_DELAY)

    def print_output_lines(self, lines: list[OutputLine], default_color: str) -> None:
        """Print output lines with per-line color support."""
        for line in lines:
            if isinstance(line, ColoredLine):
                color = ANSI_COLORS.get(line.color or "", default_color)
                self.output(f"{color}{line.text}{RESET}\r\n")
            else:
                self.output(f"{default_color}{line}{RESET}\r\n")
            self.advance(OUTPUT_LINE_DELAY)


def _emit_shell(w: CastWriter, beat: ShellBeat, theme: ThemeConfig) -> None:
    w.output(f"{theme.prompt_color}$ {RESET}")
    w.type_text(beat.command, char_delay=beat.typing_speed)
    w.newline()
    if beat.output:
        w.print_output_lines(beat.output, theme.output_color)
    w.advance(beat.pause_after)


def _emit_app(w: CastWriter, beat: AppBeat, theme: ThemeConfig) -> None:
    w.output(f"{theme.highlight_color}>{RESET} ")
    w.type_text(beat.command, char_delay=beat.typing_speed)
    w.newline()
    if beat.output:
        w.print_output_lines(beat.output, theme.output_color)
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
