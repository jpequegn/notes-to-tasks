# CLAUDE.md — Implementation B (Pure Markdown)

## Session start

You're working with Implementation B: pure markdown task files, zero dependencies.

Tasks live in `implementations/B-pure-markdown/tasks/`. Each file = one task.

Read `../../SCHEMA.md` for the canonical frontmatter spec.

## Reading tasks

```bash
# List all todo tasks, sorted by score
python3 daily-brief.py

# Or read task files directly
ls tasks/
cat tasks/TASK-001.md
```

**Priority order:** sort by `score` descending. Score ≥ 7 = high priority.

## Picking the next task

1. Run `python3 daily-brief.py` to see today's priorities
2. Pick the highest-score task with `status: todo` and no unresolved `dependencies`
3. Set `status: in-progress` in the frontmatter before starting
4. Work on it
5. Set `status: done` + `updated_date: YYYY-MM-DD` when complete

## Creating a task manually

Copy this template to `tasks/TASK-NNN.md` (increment NNN):

```yaml
---
id: TASK-NNN
title: "Your task title here"
status: todo
assignee: "@you"
priority: medium
score: null
urgency: null
impact: null
effort: null
created_date: "YYYY-MM-DD"
updated_date: "YYYY-MM-DD"
due_date: null
labels: []
dependencies: []
source: "[[YYYY-MM-DD meeting-name]]"
confidence: 1.0
---

# Your task title here

## Context

## Acceptance criteria

## Notes
```

Then run: `python3 ../../scripts/score_tasks.py --impl B`

## Extracting tasks from a meeting note

```bash
python3 ../../scripts/extract_tasks.py ../../meeting-notes/YYYY-MM-DD-name.md --impl B
```

Review `../../flagged/` for tasks with confidence < 0.7 before promoting them.

## Scoring

```bash
python3 ../../scripts/score_tasks.py --impl B          # score all tasks
python3 ../../scripts/score_tasks.py --impl B --dry-run # preview only
```

Score formula: `(urgency × 0.4) + (impact × 0.4) - (effort × 0.2)`

## Updating task status

Edit the task file's frontmatter directly. Always update `updated_date`.

Valid statuses: `todo` | `in-progress` | `review` | `done` | `blocked`

If blocking: add `blocked_by: "TASK-NNN or external dependency description"` to frontmatter.
