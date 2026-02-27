# CODEX.md — OpenAI Codex Configuration

## Context

This repo extracts and scores tasks from meeting notes. Read `AGENTS.md` and `SCHEMA.md` first.

## Task schema

Tasks are markdown files with YAML frontmatter. See `SCHEMA.md` for the full spec.

Key fields: `id`, `title`, `status`, `score`, `urgency`, `impact`, `effort`, `assignee`, `source`.

Score formula: `(urgency × 0.4) + (impact × 0.4) - (effort × 0.2)` — always computed, never set manually.

## File conventions

- One task per file: `TASK-NNN.md`
- Location depends on implementation:
  - A: `implementations/A-mcp-server/tasks/`
  - B: `implementations/B-pure-markdown/tasks/`
  - C: managed by Backlog.md CLI in `implementations/C-backlog-md/backlog/`
- Meeting notes: `meeting-notes/YYYY-MM-DD-name.md`
- Flagged (low confidence): `flagged/TASK-NNN.md`

## Scoring approach

The scoring engine (`scripts/score_tasks.py`) uses:
- **Urgency** — rule-based: deadline days remaining, keyword detection ("ASAP", "blocking", "critical")
- **Impact + Effort** — LLM-scored against rubrics defined in `scripts/prompts/`

Run scoring after any task changes: `python scripts/score_tasks.py`

## Extraction pipeline

```bash
python3 scripts/extract_tasks.py meeting-notes/<file>.md
# → writes task files to implementations/<active>/tasks/
# → writes low-confidence tasks to flagged/
```
