# PI_AGENT.md — Pi Coding Agent Configuration

## Context

This repo extracts and scores tasks from meeting notes. Read `AGENTS.md` and `SCHEMA.md` first.

## Picking the next task

1. Read all files in `implementations/B-pure-markdown/tasks/` (or your active implementation)
2. Filter to `status: todo` tasks
3. Sort by `score` descending
4. Pick the highest score that you can work on (no unresolved dependencies)

## Task completion protocol

When you finish a task:
1. Set `status: done` in the task's frontmatter
2. Set `updated_date` to today's date
3. Run `python scripts/score_tasks.py` to refresh scores
4. Commit: `git commit -m "complete TASK-NNN: <title>"`

## Creating tasks from meeting notes

```bash
python3 scripts/extract_tasks.py meeting-notes/<file>.md
```

Review `flagged/` directory for low-confidence extractions before promoting to the task queue.

## Score interpretation

| Score | Priority |
|---|---|
| 8–10 | Critical — do first |
| 6–8 | High — do today |
| 4–6 | Medium — do this week |
| 0–4 | Low — backlog |

## Schema reference

See `SCHEMA.md` for frontmatter fields. Key fields: `id`, `title`, `status`, `score`, `assignee`.
