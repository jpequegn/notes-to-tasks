# notes-to-tasks

AI-scored markdown task tracker — 3-architecture investigation project.

## What this is

Meeting notes contain tasks. This repo investigates the best way to **extract, score, and share**
those tasks across a dev team, with first-class support for AI coding agents (Claude Code, Gemini
CLI, Pi, Codex).

**Target:** solo developers and dev teams of 1–15. Above that, use Linear.

## The 3 Architectures

| | A — MCP Server | B — Pure Markdown | C — Backlog.md |
|---|---|---|---|
| **Dependencies** | Python + MCP SDK | None | Backlog.md CLI |
| **Agent access** | Typed tool calls | File read/write | Backlog.md MCP |
| **UI** | None (agent-native) | Any editor | Kanban board |
| **Best for** | Claude Code power users | Any agent, zero setup | Teams wanting a UI |
| **Path** | `implementations/A-mcp-server/` | `implementations/B-pure-markdown/` | `implementations/C-backlog-md/` |

## Shared across all implementations

- **SCHEMA.md** — canonical task frontmatter spec
- **meeting-notes/** — source documents (one file per meeting)
- **scripts/** — extraction + scoring pipeline (Python)
- **AGENTS.md** — universal instructions for all AI agents

## How to choose

Start with **B (pure markdown)** — zero setup, works with any agent today.
Graduate to **A (MCP server)** if you want structured tool calls from Claude Code.
Try **C (Backlog.md)** if your team wants a Kanban UI alongside AI access.

## Quick start

```bash
# Extract tasks from a meeting note
python scripts/extract_tasks.py meeting-notes/your-note.md

# Score all tasks
python scripts/score_tasks.py --dry-run

# See today's priorities (Implementation B)
python implementations/B-pure-markdown/daily-brief.py
```

## Evaluation

After running all 3 implementations, see `docs/EVALUATION.md` for the comparison matrix.
