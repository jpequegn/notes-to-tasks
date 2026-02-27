# Implementation C — Backlog.md Wrapper

## What this is

An AI scoring layer on top of [Backlog.md](https://github.com/backlog-md/backlog.md) — a
markdown-native task manager with an MCP server, Kanban UI, and Claude Code integration.

This implementation adds the `score` field from SCHEMA.md on top of Backlog.md's native task
format, and provides an importer to pull tasks from meeting notes.

## Prerequisites

```bash
# Install Backlog.md CLI
npm install -g backlog.md

# Initialize in this directory
cd implementations/C-backlog-md
backlog init
```

## Setup

```bash
cd implementations/C-backlog-md

# Import tasks from a meeting note
python3 importer.py ../../meeting-notes/your-note.md

# Score all tasks (adds/updates score in frontmatter)
python3 scorer.py

# See priorities
python3 scorer.py --list

# Open Kanban UI
backlog board
```

## Directory structure

```
C-backlog-md/
├── backlog/        # Backlog.md native directory (managed by backlog CLI)
├── scorer.py       # AI scoring layer (reads backlog tasks, adds score field)
├── importer.py     # Meeting note → Backlog.md task pipeline
└── README.md
```

## MCP integration

Backlog.md ships with an MCP server. Add to Claude Code:

```json
{
  "mcpServers": {
    "backlog": {
      "command": "backlog",
      "args": ["mcp"],
      "cwd": "/path/to/implementations/C-backlog-md"
    }
  }
}
```

Claude Code can then use Backlog.md's native MCP tools alongside the AI scoring layer.

## Scoring

The `scorer.py` script reads tasks from `backlog/` and adds a `score` field using the same
formula as the other implementations: `(urgency × 0.4) + (impact × 0.4) - (effort × 0.2)`.

## Trade-offs vs other implementations

- **Most features** — Kanban UI, MCP, native Claude Code integration
- **External dependency** — requires Backlog.md CLI (`npm install -g backlog.md`)
- **Different native schema** — Backlog.md has its own frontmatter; scorer adds `score` on top
- **Best for:** teams that want a visual Kanban board alongside AI agent access
