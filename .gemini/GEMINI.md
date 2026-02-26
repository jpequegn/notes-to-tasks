# GEMINI.md — Gemini CLI Configuration

## Context

This repo extracts and scores tasks from meeting notes. Read `AGENTS.md` and `SCHEMA.md` first.

## Task schema

Tasks use YAML frontmatter (see `SCHEMA.md`). Score formula:
`score = (urgency × 0.4) + (impact × 0.4) - (effort × 0.2)`

Never set `score` manually — use `python scripts/score_tasks.py`.

## File locations

```
meeting-notes/          # Source documents
implementations/
  A-mcp-server/tasks/   # Tasks for Implementation A
  B-pure-markdown/tasks/ # Tasks for Implementation B
  C-backlog-md/backlog/  # Tasks for Implementation C
scripts/extract_tasks.py # Meeting note → task JSON
scripts/score_tasks.py   # Scoring engine
```

## Workflow

```bash
# Extract tasks from a meeting note
python scripts/extract_tasks.py meeting-notes/<file>.md

# Score tasks
python scripts/score_tasks.py

# See priorities (Implementation B)
python implementations/B-pure-markdown/daily-brief.py
```

## When reading tasks

Sort by `score` descending for priority order. A score ≥ 7 is high priority. Tasks marked
`status: blocked` require `blocked_by` to be resolved before work can proceed.

## When creating tasks

Follow the frontmatter spec in `SCHEMA.md` exactly. Auto-increment the `id` (check existing
task files for the highest TASK-NNN). Set `confidence` based on how clear the action item was
in the meeting notes (0.0–1.0). Tasks with `confidence < 0.7` go to `flagged/` directory.
