# pipeline/schema.py
"""Scene and beat pydantic models with validation."""
from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from .errors import SchemaError

MAX_BEATS = 50
MAX_DURATION_S = 180.0


class ColoredLine(BaseModel):
    """A single output line with optional ANSI color."""

    text: str
    color: str | None = None  # ANSI name: red, green, yellow, blue, magenta, cyan, dim, bold


# Output line: plain string or colored object
OutputLine = Union[str, ColoredLine]


class SceneConfig(BaseModel):
    """Global scene configuration."""

    cols: int = 100
    rows: int = 30
    shell_prompt: str = "$ "
    app_prompt: str = "> "
    theme: str = "default"
    title: str = "Demo"
    seed: int | None = None
    # agg pass-through options
    speed: float | None = None
    fps_cap: int | None = None
    idle_time_limit: float | None = None
    last_frame_duration: float | None = None
    no_loop: bool = False
    font_family: str | None = None
    line_height: float | None = None
    # PII
    pii_allow: list[str] = Field(default_factory=list)


class ShellBeat(BaseModel):
    type: Literal["shell"]
    command: str
    output: list[OutputLine] = Field(default_factory=list)
    pause_after: float = 1.0
    typing_speed: float | None = None  # override CHAR_DELAY


class AppBeat(BaseModel):
    type: Literal["app"]
    app_name: str
    command: str
    output: list[OutputLine] = Field(default_factory=list)
    pause_after: float = 2.0
    typing_speed: float | None = None


class ClearBeat(BaseModel):
    type: Literal["clear"]


class CommentBeat(BaseModel):
    type: Literal["comment"]
    text: str


class PauseBeat(BaseModel):
    type: Literal["pause"]
    duration: float = 1.0


Beat = Annotated[
    Union[ShellBeat, AppBeat, ClearBeat, CommentBeat, PauseBeat],
    Field(discriminator="type"),
]


class Scene(BaseModel):
    """Top-level scene model."""

    version: str
    config: SceneConfig = Field(default_factory=SceneConfig)
    beats: list[Beat]

    @field_validator("beats")
    @classmethod
    def check_max_beats(cls, v: list[Beat]) -> list[Beat]:
        if len(v) > MAX_BEATS:
            raise ValueError(f"Max {MAX_BEATS} beats allowed, got {len(v)}")
        return v

    @model_validator(mode="after")
    def check_max_duration(self) -> Scene:
        total = 0.0
        for beat in self.beats:
            if hasattr(beat, "pause_after"):
                total += beat.pause_after
            elif hasattr(beat, "duration"):
                total += beat.duration
        if total > MAX_DURATION_S:
            raise ValueError(
                f"Max {MAX_DURATION_S}s total duration, got {total:.1f}s"
            )
        return self


def validate_scene(data: dict[str, object]) -> Scene:
    """Validate a raw dict as a Scene. Raises SchemaError on failure."""
    try:
        return Scene.model_validate(data)
    except Exception as e:
        raise SchemaError(str(e)) from e
