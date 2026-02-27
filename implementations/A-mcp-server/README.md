# Implementation A — MCP Server + Markdown Files

## What this is

A local MCP server that exposes task CRUD as typed tool calls. Claude Code connects to this
server and can create, list, update, and score tasks without reading markdown files directly.

## Setup

```bash
cd implementations/A-mcp-server

# Install dependencies
pip3 install mcp pyyaml

# Start the server (adds it to Claude Code's MCP config)
python3 server.py --install

# Or run directly
python3 server.py
```

## MCP tools

| Tool | Description | Parameters |
|---|---|---|
| `list_tasks` | List tasks with filters | `status`, `assignee`, `label`, `min_score`, `max_score` |
| `create_task` | Create a new task file | `title`, `assignee`, `priority`, `due_date`, `labels`, `source` |
| `update_task` | Patch task frontmatter | `id`, + any frontmatter fields to update |
| `complete_task` | Mark a task done | `id` |
| `score_tasks` | Re-run scoring pipeline | `dry_run` (optional) |

## Directory structure

```
A-mcp-server/
├── tasks/          # One TASK-NNN.md file per task
├── flagged/        # Low-confidence extractions awaiting review
├── server.py       # MCP server (run this)
├── mcp.json        # Claude Code MCP config reference
└── README.md
```

## Connecting to Claude Code

After running `python server.py --install`, add to your `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "notes-to-tasks": {
      "command": "python",
      "args": ["/absolute/path/to/implementations/A-mcp-server/server.py"]
    }
  }
}
```

## Why this approach

- Claude Code gets typed tool calls instead of raw file access
- Tasks are queryable (filter by score, status, assignee)
- Scoring runs in-server, not as a separate script
- Lays groundwork for syncing to GitHub Issues MCP (official MCP server exists)

## Trade-offs vs other implementations

- **More setup** than B (pure markdown)
- **More structured** — agents can't accidentally corrupt frontmatter
- **Requires Python runtime** to be running
- **Best for:** teams doing most work through Claude Code
