"""Tests for asciicast v2 renderer."""
from __future__ import annotations

from pipeline.renderer import Event, render
from pipeline.schema import validate_scene
from pipeline.themes import ThemeConfig


def _scene(beats: list[dict], seed: int | None = None) -> dict:
    cfg = {"seed": seed} if seed is not None else {}
    return {"version": "1.0", "config": cfg, "beats": beats}


class TestRenderFormat:
    def test_returns_event_list(self):
        scene = validate_scene(_scene([{"type": "shell", "command": "echo hi", "output": ["hi"]}]))
        events = render(scene, ThemeConfig())
        assert isinstance(events, list)
        assert all(isinstance(e, Event) for e in events)

    def test_event_has_timestamp_and_data(self):
        scene = validate_scene(_scene([{"type": "shell", "command": "echo hi", "output": ["hi"]}]))
        events = render(scene, ThemeConfig())
        for e in events:
            assert isinstance(e.time, float)
            assert e.time >= 0.0
            assert isinstance(e.type, str)
            assert isinstance(e.data, str)

    def test_timestamps_monotonic(self):
        scene = validate_scene(_scene([
            {"type": "shell", "command": "a", "output": ["x"]},
            {"type": "shell", "command": "b", "output": ["y"]},
        ]))
        events = render(scene, ThemeConfig())
        times = [e.time for e in events]
        assert times == sorted(times)


class TestBeatTypes:
    def test_shell_beat_has_prompt_and_command(self):
        scene = validate_scene(_scene([{"type": "shell", "command": "ls", "output": ["file.txt"]}]))
        events = render(scene, ThemeConfig())
        text = "".join(e.data for e in events)
        assert "ls" in text
        assert "file.txt" in text

    def test_app_beat_has_app_prompt(self):
        scene = validate_scene(_scene([
            {"type": "app", "app_name": "claude", "command": "/help", "output": ["Help text"]}
        ]))
        events = render(scene, ThemeConfig())
        text = "".join(e.data for e in events)
        assert "/help" in text
        assert "Help text" in text

    def test_clear_beat_emits_escape(self):
        scene = validate_scene(_scene([{"type": "clear"}]))
        events = render(scene, ThemeConfig())
        text = "".join(e.data for e in events)
        assert "\x1b[2J" in text

    def test_comment_beat_appears_dim(self):
        scene = validate_scene(_scene([{"type": "comment", "text": "# hello"}]))
        events = render(scene, ThemeConfig())
        text = "".join(e.data for e in events)
        assert "# hello" in text
        assert "\x1b[90m" in text

    def test_pause_beat_advances_time(self):
        scene = validate_scene(_scene([
            {"type": "shell", "command": "a", "output": []},
            {"type": "pause", "duration": 5.0},
            {"type": "shell", "command": "b", "output": []},
        ]))
        events = render(scene, ThemeConfig())
        found_a = False
        time_after_a = 0.0
        time_at_b = 0.0
        for e in events:
            if "a" in e.data and not found_a:
                found_a = True
                time_after_a = e.time
            if found_a and "b" in e.data:
                time_at_b = e.time
                break
        assert time_at_b - time_after_a >= 5.0


class TestDeterminism:
    def test_same_seed_same_output(self):
        data = _scene([{"type": "shell", "command": "echo test", "output": ["test"]}], seed=42)
        scene = validate_scene(data)
        theme = ThemeConfig()
        events_a = render(scene, theme)
        events_b = render(scene, theme)
        assert len(events_a) == len(events_b)
        for a, b in zip(events_a, events_b):
            assert a.time == b.time
            assert a.data == b.data


class TestEmptyScene:
    def test_empty_beats(self):
        scene = validate_scene({"version": "1.0", "beats": []})
        events = render(scene, ThemeConfig())
        assert events == []
