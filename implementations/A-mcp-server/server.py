#!/usr/bin/env python3
"""
Implementation A — MCP Server for notes-to-tasks

Exposes task CRUD as MCP tool calls for Claude Code and other MCP-capable agents.

Requirements:
    pip install mcp pyyaml

Usage:
    python server.py           # Run MCP server (stdio transport)
    python server.py --install # Add to .claude/mcp.json and exit
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

IMPL_DIR = Path(__file__).parent
TASKS_DIR = IMPL_DIR / "tasks"
FLAGGED_DIR = IMPL_DIR / "flagged"
REPO_ROOT = IMPL_DIR.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 4:].strip()
    if HAS_YAML:
        try:
            fm = yaml.safe_load(fm_text) or {}  # type: ignore[possibly-undefined]
        except yaml.YAMLError:  # type: ignore[possibly-undefined]
            fm = {}
    else:
        fm = _minimal_yaml_parse(fm_text)
    return fm, body


def _minimal_yaml_parse(text: str) -> dict:
    fm: dict = {}
    for line in text.splitlines():
        m = re.match(r'^(\w[\w_-]*):\s*(.+)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip().strip('"\'')
            if val.lower() in ("null", "~"):
                fm[key] = None
            elif re.match(r'^\d+\.\d+$', val):
                fm[key] = float(val)
            elif re.match(r'^\d+$', val):
                fm[key] = int(val)
            else:
                fm[key] = val
    return fm


def render_frontmatter(fm: dict) -> str:
    lines = []
    for key, val in fm.items():
        if val is None:
            lines.append(f"{key}: null")
        elif isinstance(val, list):
            lines.append(f"{key}: {json.dumps(val)}")
        elif isinstance(val, str):
            # Guard: if a string looks like a JSON array (corrupted round-trip),
            # parse it back to a list and emit properly.
            stripped = val.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    import json as _j
                    parsed = _j.loads(stripped)
                    if isinstance(parsed, list):
                        lines.append(f"{key}: {json.dumps(parsed)}")
                        continue
                except ValueError:
                    pass
            lines.append(f'{key}: "{val}"')
        elif isinstance(val, float):
            lines.append(f"{key}: {val:.1f}")
        else:
            lines.append(f"{key}: {val}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Task operations
# ---------------------------------------------------------------------------

def next_task_id() -> str:
    existing = list(TASKS_DIR.glob("TASK-*.md")) + list(FLAGGED_DIR.glob("TASK-*.md"))
    nums = []
    for f in existing:
        m = re.match(r"TASK-(\d+)", f.stem)
        if m:
            nums.append(int(m.group(1)))
    return f"TASK-{(max(nums) + 1):03d}" if nums else "TASK-001"


def load_all_tasks() -> list[dict]:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    tasks = []
    for path in sorted(TASKS_DIR.glob("TASK-*.md")):
        text = path.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)
        if fm:
            fm["_path"] = str(path)
            tasks.append(fm)
    return tasks


def write_task_file(task_id: str, fm: dict, body: str = "") -> Path:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    path = TASKS_DIR / f"{task_id}.md"
    title = fm.get("title", task_id)
    if not body:
        body = f"# {title}\n\n> Run `python3 scripts/score_tasks.py` to compute final score.\n\n## Context\n\n## Acceptance criteria\n\n## Notes\n"
    content = f"---\n{render_frontmatter(fm)}\n---\n\n{body}"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def tool_list_tasks(params: dict) -> str:
    tasks = load_all_tasks()
    status_filter = params.get("status")
    assignee_filter = params.get("assignee")
    label_filter = params.get("label")
    min_score = params.get("min_score")
    max_score = params.get("max_score")

    filtered = []
    for t in tasks:
        if status_filter and t.get("status") != status_filter:
            continue
        if assignee_filter and t.get("assignee") != assignee_filter:
            continue
        if label_filter:
            labels = t.get("labels") or []
            if isinstance(labels, str):
                labels = [labels]
            if label_filter not in labels:
                continue
        score = t.get("score")
        if min_score is not None and (score is None or score < min_score):
            continue
        if max_score is not None and (score is not None and score > max_score):
            continue
        filtered.append(t)

    filtered.sort(key=lambda t: (t.get("score") or 0), reverse=True)

    if not filtered:
        return "No tasks found matching the given filters."

    lines = [f"Found {len(filtered)} task(s):\n"]
    for t in filtered:
        score = t.get("score")
        score_str = f"{score:.1f}" if score is not None else "unscored"
        lines.append(
            f"  {t.get('id', '?')}  [{score_str}]  {t.get('status', '?')}  "
            f"{t.get('assignee', 'unassigned')}  {t.get('title', '')}"
        )
    return "\n".join(lines)


def tool_create_task(params: dict) -> str:
    today = date.today().isoformat()
    task_id = next_task_id()

    fm = {
        "id": task_id,
        "title": params.get("title", "Untitled task"),
        "status": "todo",
        "assignee": params.get("assignee", "unassigned"),
        "priority": params.get("priority", "medium"),
        "score": None,
        "urgency": None,
        "impact": None,
        "effort": None,
        "created_date": today,
        "updated_date": today,
        "due_date": params.get("due_date", None),
        "labels": params.get("labels", []),
        "dependencies": params.get("dependencies", []),
        "source": params.get("source", "manual"),
        "confidence": params.get("confidence", 1.0),
    }

    path = write_task_file(task_id, fm)
    return f"Created {task_id}: {fm['title']}\nFile: {path}\nRun score_tasks to compute score."


def tool_update_task(params: dict) -> str:
    task_id = params.get("id")
    if not task_id:
        return "Error: 'id' is required"

    path = TASKS_DIR / f"{task_id}.md"
    if not path.exists():
        return f"Error: task {task_id} not found"

    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    update_fields = {k: v for k, v in params.items() if k != "id"}
    fm.update(update_fields)
    fm["updated_date"] = date.today().isoformat()

    content = f"---\n{render_frontmatter(fm)}\n---\n\n{body}"
    path.write_text(content, encoding="utf-8")
    return f"Updated {task_id}: {', '.join(update_fields.keys())}"


def tool_complete_task(params: dict) -> str:
    task_id = params.get("id")
    if not task_id:
        return "Error: 'id' is required"

    path = TASKS_DIR / f"{task_id}.md"
    if not path.exists():
        return f"Error: task {task_id} not found"

    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    today = date.today().isoformat()
    fm["status"] = "done"
    fm["updated_date"] = today
    fm["completed_date"] = today

    content = f"---\n{render_frontmatter(fm)}\n---\n\n{body}"
    path.write_text(content, encoding="utf-8")
    return f"Completed {task_id}: {fm.get('title', '')}"


def tool_score_tasks(params: dict) -> str:
    dry_run = params.get("dry_run", False)
    score_script = SCRIPTS_DIR / "score_tasks.py"
    if not score_script.exists():
        return f"Error: scoring script not found at {score_script}"

    import subprocess
    cmd = [sys.executable, str(score_script), "--impl", "A"]
    if dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    output = result.stdout + result.stderr
    return output if output else "Scoring complete (no output)"


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "list_tasks",
        "description": "List tasks with optional filters. Returns tasks sorted by score descending.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["todo", "in-progress", "review", "done", "blocked"],
                           "description": "Filter by status"},
                "assignee": {"type": "string", "description": "Filter by @username or 'unassigned'"},
                "label": {"type": "string", "description": "Filter by label"},
                "min_score": {"type": "number", "description": "Minimum score (inclusive)"},
                "max_score": {"type": "number", "description": "Maximum score (inclusive)"},
            },
        },
    },
    {
        "name": "create_task",
        "description": "Create a new task file from structured input.",
        "inputSchema": {
            "type": "object",
            "required": ["title"],
            "properties": {
                "title": {"type": "string", "description": "Task title (imperative verb phrase)"},
                "assignee": {"type": "string", "description": "@username or 'unassigned'"},
                "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                "due_date": {"type": "string", "description": "YYYY-MM-DD or null"},
                "labels": {"type": "array", "items": {"type": "string"}},
                "dependencies": {"type": "array", "items": {"type": "string"},
                                 "description": "List of TASK-NNN ids this depends on"},
                "source": {"type": "string", "description": "Wikilink to source meeting note"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
        },
    },
    {
        "name": "update_task",
        "description": "Patch frontmatter fields on an existing task.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string", "description": "Task ID (e.g. TASK-001)"},
                "status": {"type": "string", "enum": ["todo", "in-progress", "review", "done", "blocked"]},
                "assignee": {"type": "string"},
                "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                "due_date": {"type": "string"},
                "labels": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    {
        "name": "complete_task",
        "description": "Mark a task as done. Sets status:done and completed_date to today.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string", "description": "Task ID (e.g. TASK-001)"},
            },
        },
    },
    {
        "name": "score_tasks",
        "description": "Re-run the scoring pipeline on all tasks in Implementation A.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dry_run": {"type": "boolean", "description": "Preview scores without writing"},
            },
        },
    },
]


def run_server():
    if not HAS_MCP:
        print("Error: mcp package not installed. Run: pip3 install mcp pyyaml", file=sys.stderr)
        sys.exit(1)

    server = Server("notes-to-tasks")

    @server.list_tools()
    async def list_tools():
        return [Tool(
            name=t["name"],
            description=t["description"],
            inputSchema=t["inputSchema"],
        ) for t in TOOLS]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        dispatch = {
            "list_tasks": tool_list_tasks,
            "create_task": tool_create_task,
            "update_task": tool_update_task,
            "complete_task": tool_complete_task,
            "score_tasks": tool_score_tasks,
        }
        fn = dispatch.get(name)
        if fn is None:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        result = fn(arguments or {})
        return [TextContent(type="text", text=result)]

    import asyncio

    async def _main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(_main())


def install():
    """Add this server to .claude/mcp.json in the repo root."""
    mcp_dir = REPO_ROOT / ".claude"
    mcp_dir.mkdir(exist_ok=True)
    mcp_json = mcp_dir / "mcp.json"

    config = {}
    if mcp_json.exists():
        try:
            config = json.loads(mcp_json.read_text())
        except json.JSONDecodeError:
            pass

    config.setdefault("mcpServers", {})
    config["mcpServers"]["notes-to-tasks"] = {
        "command": sys.executable,
        "args": [str(Path(__file__).resolve())],
    }

    mcp_json.write_text(json.dumps(config, indent=2))
    print(f"Installed MCP server config to {mcp_json}")
    print("Restart Claude Code to pick up the new MCP server.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true", help="Install MCP config and exit")
    args = parser.parse_args()

    if args.install:
        install()
    else:
        run_server()
