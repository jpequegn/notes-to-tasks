# CLAUDE.md — Claude Code Configuration

## Session start protocol

1. Read `AGENTS.md` — universal context for this repo
2. Read `SCHEMA.md` — task frontmatter spec
3. Check `gh issue list` — see current build status
4. Check which implementation you're working in (A, B, or C)

## MCP setup (Implementation A)

When working with Implementation A, add the local MCP server to Claude Code:

```json
// .claude/mcp.json (created by `cd implementations/A-mcp-server && python server.py --install`)
{
  "mcpServers": {
    "notes-to-tasks": {
      "command": "python",
      "args": ["implementations/A-mcp-server/server.py"],
      "cwd": "/path/to/notes-to-tasks"
    }
  }
}
```

### Available MCP tools (Implementation A)

| Tool | Description |
|---|---|
| `list_tasks` | Filter by status, assignee, label, score range |
| `create_task` | Write a new .md task file from structured JSON |
| `update_task` | Patch frontmatter fields on an existing task |
| `complete_task` | Set status:done + completed_date |
| `score_tasks` | Re-run scoring pipeline on all tasks |

## Working with tasks (Implementation B — pure markdown)

Tasks live in `implementations/B-pure-markdown/tasks/`. Each file = one task.

**To create a task:**
```bash
# Use the schema from SCHEMA.md, write to tasks/TASK-NNN.md
# Then run scoring:
python scripts/score_tasks.py
```

**To complete a task:** Set `status: done` and `updated_date` in the frontmatter.

**To see today's priorities:**
```bash
python implementations/B-pure-markdown/daily-brief.py
```

## Extraction workflow

```bash
# 1. Add a meeting note
cp meeting-notes/TEMPLATE.md meeting-notes/$(date +%Y-%m-%d)-meeting-name.md
# ... fill it in ...

# 2. Extract tasks
python scripts/extract_tasks.py meeting-notes/$(date +%Y-%m-%d)-meeting-name.md

# 3. Review flagged tasks (confidence < 0.7)
ls flagged/

# 4. Score everything
python scripts/score_tasks.py
```

## Quality rules

- Never commit `score` values set manually — always run `score_tasks.py`
- Tasks in `flagged/` need human review before moving to the active task queue
- `source` field must reference an existing meeting note file
- Keep `updated_date` current when patching task frontmatter
