```
          __            __
   ____ _/ /_  ______  / /_
  / __ `/ / / / / __ \/ __ \
 / /_/ / / /_/ / /_/ / / / /
 \__, /_/\__, / .___/_/ /_/
/____/  /____/_/
```

**Generate terminal demo GIFs from natural language.**

[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-5b21b6?style=flat-square)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> No real commands executed — everything is synthetic. Polished asciicast recordings with realistic typing, configurable themes, and built-in PII auditing.

---

## Install

<!-- INSTALL:START — auto-synced from emporium/INSTALL_REFERENCE.md -->
```bash
claude plugin marketplace add heurema/emporium
claude plugin install glyph@emporium
```
<!-- INSTALL:END -->

## Commands

| Command | What it does |
|---------|-------------|
| `/glyph "description"` | Generate a demo GIF from a natural language description |
| `/glyph` | Interactive mode — asks what to demo |
| `/glyph themes` | List available themes |
| `/glyph preview <path>` | Render an existing scene JSON to GIF |

## How It Works

```
description → scene JSON → asciicast v2 → PII audit → .cast → agg → .gif
```

1. **Scene generation**: Claude creates a scene JSON from your description — shell commands, app interactions, comments, pauses
2. **Rendering**: Converts beats to asciicast v2 events with realistic typing timing (seeded RNG for reproducibility)
3. **PII audit**: Scans output for home paths, emails, API keys, secrets — blocks if found
4. **GIF conversion**: Pipes `.cast` through [agg](https://github.com/asciinema/agg) to produce the final GIF

## Scene Format

```json
{
  "version": "1.0",
  "config": {
    "cols": 100, "rows": 30,
    "shell_prompt": "$ ",
    "theme": "default",
    "title": "My Demo",
    "seed": 42
  },
  "beats": [
    {"type": "shell", "command": "cargo build", "output": ["Compiling myapp v0.2.0"], "pause_after": 1.0},
    {"type": "comment", "text": "# Build complete"},
    {"type": "pause", "duration": 2.0},
    {"type": "clear"}
  ]
}
```

Beat types: `shell`, `app`, `comment`, `clear`, `pause`.

Limits: max 50 beats, max 120s total duration.

## Themes

Two built-in themes:

| Theme | Description |
|-------|-------------|
| `default` | Monokai colors, standard terminal look |
| `amber` | Retro amber-on-black CRT style |

Custom themes: create a JSON file with `prompt_color`, `output_color`, `comment_color`, `highlight_color`, `agg_theme`, `agg_font_size` and pass it via `--theme /path/to/theme.json`.

## Requirements

- Python 3.10+
- [agg](https://github.com/asciinema/agg) — for GIF output (`brew install agg` or `cargo install agg`)
- Claude Code

Without `agg`, the pipeline produces `.cast` files (viewable with `asciinema play`).

## Privacy

- No real shell commands are executed
- PII audit blocks output containing home paths, emails, API keys, or secrets
- All data stays local

## License

MIT
