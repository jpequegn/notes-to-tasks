# Implementation B — Pure Markdown

## What this is

Zero-dependency task tracking. Tasks are markdown files with YAML frontmatter. Any AI agent
with file access can read and write them. This is the recommended starting point.

## Setup

No setup required. Just start using it.

```bash
# Extract tasks from a meeting note
python3 ../../scripts/extract_tasks.py ../../meeting-notes/your-note.md --impl B

# Score tasks
python3 ../../scripts/score_tasks.py --impl B

# See today's priorities
python3 daily-brief.py
```

## Directory structure

```
B-pure-markdown/
├── tasks/          # TASK-NNN.md files (one per task)
├── flagged/        # Low-confidence extractions awaiting review
├── CLAUDE.md       # Claude Code session instructions for this implementation
├── daily-brief.py  # Generate priority view
└── README.md
```

## How Claude Code uses this

On session start, Claude Code reads `CLAUDE.md` → knows the task schema, file locations, and
workflow. From there it can:

- Read `tasks/` to see all tasks
- Sort by `score` to prioritize
- Edit frontmatter to update status
- Run `daily-brief.py` to get a formatted summary

## Why this approach

- **Zero dependencies** — works today with any AI agent
- **Transparent** — tasks are plain markdown files, readable in any editor
- **Portable** — works with Claude Code, Gemini CLI, Cursor, VS Code, Obsidian
- **The "vibe coding" pattern** — tasks become executable prompts for AI agents

## Full usage guide

See [`docs/USAGE.md — Implementation B`](../../docs/USAGE.md#implementation-b--pure-markdown) for
detailed create / update / delete examples and vault insight prompt templates.

## Trade-offs vs other implementations

- **No typed tool calls** — agents must parse frontmatter themselves
- **No structured queries** — filtering requires reading all files
- **Best for:** solo developers and 1–3 person teams
