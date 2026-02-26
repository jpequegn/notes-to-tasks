# AGENTS.md — Universal Agent Instructions

All AI agents working in this repo should read this file first.

## What this repo is

Meeting notes → structured tasks → scored priority queue. Three parallel implementations let us
evaluate which architecture works best for small dev teams (1–15 people).

## Repo map

```
SCHEMA.md              ← task frontmatter spec (read this)
meeting-notes/         ← source documents, one file per meeting
scripts/               ← shared extraction + scoring pipeline
implementations/
  A-mcp-server/        ← MCP server + markdown files
  B-pure-markdown/     ← pure markdown, zero deps
  C-backlog-md/        ← Backlog.md wrapper
docs/EVALUATION.md     ← comparison matrix (fill in as you test)
```

## Task schema

See `SCHEMA.md` for the canonical frontmatter spec. All implementations use the same schema.

**Score formula:** `(urgency × 0.4) + (impact × 0.4) - (effort × 0.2)`

**Never manually set `score`** — it is always computed by `scripts/score_tasks.py`.

## Meeting note format

See `meeting-notes/TEMPLATE.md`. Key sections:
- Attendees, date, agenda
- Discussion (freeform)
- **Action items** — the primary extraction source
- Decisions, follow-ups

## Extracting tasks from a meeting note

```bash
python scripts/extract_tasks.py meeting-notes/<file>.md
```

Tasks with `confidence < 0.7` go to `flagged/` — review before promoting.

## Scoring tasks

```bash
python scripts/score_tasks.py              # score all tasks in active implementation
python scripts/score_tasks.py --dry-run   # preview scores without writing
```

## Agent-specific config

| Agent | Read this |
|---|---|
| Claude Code | `CLAUDE.md` |
| Gemini CLI | `.gemini/GEMINI.md` |
| Pi (pi.dev) | `PI_AGENT.md` |
| Codex | `CODEX.md` |

## Build tracker (GitHub Issues)

The 6 GitHub Issues in this repo track the build in dependency order:

1. **#1 [Setup]** — repo structure + agent config files (this file)
2. **#2 [Shared]** — SCHEMA.md + meeting template + scoring engine ← blocks #3, #4, #5
3. **#3 [Impl A]** — MCP server + markdown task store ← depends on #2
4. **#4 [Impl B]** — pure markdown + CLAUDE.md + daily brief ← depends on #2
5. **#5 [Impl C]** — Backlog.md wrapper + AI scoring layer ← depends on #2
6. **#6 [Eval]** — evaluation framework + comparison matrix ← depends on #3, #4, #5

## What not to do

- Do not modify `SCHEMA.md` frontmatter keys without updating all 3 implementations
- Do not commit tasks with `confidence < 0.7` directly to the task queue — use `flagged/`
- Do not set `score` manually — always recompute via `score_tasks.py`
