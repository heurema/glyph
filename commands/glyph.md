---
name: glyph
description: Generate terminal demo GIFs from natural language
allowed-tools: Bash, Read, Write, Glob, Grep
---

You are generating a terminal demo GIF using the glyph pipeline.

## Args Parsing

Check the user's message for subcommands:

- **`/glyph themes`**: List available themes. Read `${CLAUDE_PLUGIN_ROOT}/resources/themes/` and show each theme name + description.
- **`/glyph preview <path>`**: Render an existing scene JSON file to GIF. Run pipeline directly.
- **`/glyph "description"`** or **`/glyph`**: Generate a new scene from description (or interactively).

## Scene Generation Flow

1. **Understand what to demo**: If the user provided a description, use it. Otherwise ask: "What should the demo show? (e.g., installing a CLI tool, running a command, showing output)"

2. **Generate scene JSON**: Create a scene JSON following this schema:

```json
{
  "version": "1.0",
  "config": {
    "cols": 100,
    "rows": 30,
    "shell_prompt": "$ ",
    "app_prompt": "> ",
    "theme": "default",
    "title": "Demo Title",
    "seed": 42
  },
  "beats": [
    {"type": "shell", "command": "...", "output": ["..."], "pause_after": 1.0},
    {"type": "app", "app_name": "...", "command": "...", "output": ["..."], "pause_after": 2.0},
    {"type": "comment", "text": "# ..."},
    {"type": "clear"},
    {"type": "pause", "duration": 3.0}
  ]
}
```

Beat types: shell (command + output), app (interactive app), comment (dim text), clear (screen), pause (wait).

Constraints: max 50 beats, max 120s total pause/duration, no PII (no /Users/, /home/, ~, API keys, emails, passwords, secrets).

3. **Write scene file**: Save to a temp location.

4. **Run pipeline**:
```bash
cd "${CLAUDE_PLUGIN_ROOT}" && PYTHONPATH=. python3 -m pipeline "<scene_path>" --output "<output_dir>" 2>&1
```

5. **Handle results**:
   - Success: show the file paths and sizes
   - PII error (exit 2): fix the scene (remove PII patterns) and retry
   - Schema error (exit 1): fix the scene and retry
   - If agg not installed: show .cast path and install instructions for agg

6. **Show the GIF**: Tell the user where the GIF is saved and suggest embedding it:
   ```markdown
   ![Demo](path/to/demo.gif)
   ```
