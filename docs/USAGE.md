# Usage Guide — notes-to-tasks

Practical reference for all three implementations. Each section covers:
- **Create** — add a task (manually and from a meeting note)
- **Update** — change status, fields, or score
- **Delete** — archive or remove a task
- **Vault insights** — sample agent interactions that surface patterns across the task store

Jump to your implementation:
- [Implementation A — MCP Server](#implementation-a--mcp-server)
- [Implementation B — Pure Markdown](#implementation-b--pure-markdown)
- [Implementation C — Backlog.md](#implementation-c--backlogmd)
- [Vault Insights — querying across all tasks](#vault-insights)

---

## Implementation A — MCP Server

**When to use:** Claude Code is your primary agent and you want typed tool calls instead of
raw file access. Tasks live in `implementations/A-mcp-server/tasks/`.

### Setup

```bash
cd implementations/A-mcp-server
pip3 install -r requirements.txt          # mcp>=1.0.0, pyyaml>=6.0
python3 server.py --install               # writes .claude/mcp.json
# Restart Claude Code to pick up the MCP server
```

---

### Create a task

**Via MCP tool call (Claude Code):**

```
Tool: create_task
{
  "title": "Add rate limiting to the API",
  "assignee": "@alice",
  "priority": "high",
  "due_date": "2026-03-15",
  "labels": ["backend", "api"],
  "source": "[[2026-03-05-sprint-planning]]",
  "confidence": 0.95
}
```

Response:
```
Created TASK-001: Add rate limiting to the API
File: implementations/A-mcp-server/tasks/TASK-001.md
Run score_tasks to compute score.
```

**Then score it:**

```
Tool: score_tasks
{}
```

Response:
```
Implementation A — 1 task(s)
  Scored TASK-001: score=5.6 (u=7 i=7 e=4) — Add rate limiting to the API
```

**From a meeting note (extraction pipeline):**

```bash
# Extracts all action items and writes task files
python3 scripts/extract_tasks.py meeting-notes/2026-03-05-sprint-planning.md --impl A

# Then score
python3 scripts/score_tasks.py --impl A
```

---

### Update a task

**Change status to in-progress:**

```
Tool: update_task
{
  "id": "TASK-001",
  "status": "in-progress"
}
```

Response: `Updated TASK-001: status`

**Change multiple fields at once:**

```
Tool: update_task
{
  "id": "TASK-001",
  "status": "blocked",
  "assignee": "@bob",
  "labels": ["backend", "api", "security"]
}
```

> **Note:** When setting `status: blocked`, also set `blocked_by` in a second `update_task`
> call — the MCP tool passes any fields you include directly to the frontmatter.

```
Tool: update_task
{
  "id": "TASK-001",
  "blocked_by": "TASK-003"
}
```

**Re-score after manual field changes:**

```
Tool: score_tasks
{ "dry_run": true }    ← preview first
```

```
Tool: score_tasks
{}                     ← write
```

---

### Delete / archive a task

Implementation A has no native delete tool — tasks are markdown files. To remove:

```bash
# Archive (move out of the active queue)
mv implementations/A-mcp-server/tasks/TASK-001.md \
   implementations/A-mcp-server/flagged/TASK-001-archived.md

# Hard delete (irreversible)
rm implementations/A-mcp-server/tasks/TASK-001.md
```

Or mark it done and leave it in place (recommended — preserves history):

```
Tool: complete_task
{ "id": "TASK-001" }
```

Response: `Completed TASK-001: Add rate limiting to the API`

The task remains in `tasks/` with `status: done` and `completed_date` set. It won't appear
in filtered `list_tasks` calls that filter by `status: todo`.

---

### Common list_tasks queries

```
# All todo tasks, sorted by score
Tool: list_tasks
{ "status": "todo" }

# My tasks today
Tool: list_tasks
{ "assignee": "@alice", "status": "todo" }

# Only high-priority work (score ≥ 7)
Tool: list_tasks
{ "min_score": 7.0 }

# Backend tasks not yet done
Tool: list_tasks
{ "label": "backend", "status": "todo" }

# Blocked tasks needing attention
Tool: list_tasks
{ "status": "blocked" }
```

---

## Implementation B — Pure Markdown

**When to use:** zero-dependency setup, works with any agent (Gemini CLI, Pi, Codex, Claude
Code without MCP). Tasks live in `implementations/B-pure-markdown/tasks/`.

No server. No install. Open `tasks/` in any editor or let your agent read the files.

---

### Create a task

**Manually — copy the template:**

```bash
# Find the next task number
ls implementations/B-pure-markdown/tasks/ | sort | tail -1
# → TASK-010.md → next is TASK-011

# Create the file
cat > implementations/B-pure-markdown/tasks/TASK-011.md << 'EOF'
---
id: TASK-011
title: "Migrate database to Postgres"
status: todo
assignee: "@bob"
priority: high
score: null
urgency: null
impact: null
effort: null
created_date: "2026-03-10"
updated_date: "2026-03-10"
due_date: "2026-03-28"
labels: ["backend", "database"]
dependencies: ["TASK-007"]
blocked_by: null
source: "[[2026-03-10-arch-review]]"
confidence: 1.0
---

# Migrate database to Postgres

## Context

Currently using SQLite. Need Postgres for production multi-tenancy support.
Decision made in arch review 2026-03-10.

## Acceptance criteria

- [ ] All tables migrated with zero data loss
- [ ] CI passes against Postgres
- [ ] Connection pool configured

## Notes

Use Alembic for migrations. Start with a shadow database.
EOF

# Score immediately
python3 scripts/score_tasks.py --impl B
```

**From a meeting note:**

```bash
python3 scripts/extract_tasks.py meeting-notes/2026-03-10-arch-review.md --impl B
# → writes TASK-NNN.md for each action item (confidence ≥ 0.7)
# → writes low-confidence items to flagged/

python3 scripts/score_tasks.py --impl B
```

**Dry-run first to preview:**

```bash
python3 scripts/extract_tasks.py meeting-notes/2026-03-10-arch-review.md --impl B --dry-run
```

---

### Update a task

Tasks are plain files — edit frontmatter directly. Always update `updated_date`.

**Start work on a task:**

```bash
# Open in your editor
$EDITOR implementations/B-pure-markdown/tasks/TASK-011.md

# Or patch with sed (useful for agent scripts)
python3 - << 'EOF'
from pathlib import Path
import re, datetime

path = Path("implementations/B-pure-markdown/tasks/TASK-011.md")
today = datetime.date.today().isoformat()
text = path.read_text()
text = re.sub(r'^status:.*$', 'status: in-progress', text, flags=re.MULTILINE)
text = re.sub(r'^updated_date:.*$', f'updated_date: "{today}"', text, flags=re.MULTILINE)
path.write_text(text)
print("TASK-011 → in-progress")
EOF
```

**Block a task:**

```bash
python3 - << 'EOF'
from pathlib import Path
import re, datetime

path = Path("implementations/B-pure-markdown/tasks/TASK-011.md")
today = datetime.date.today().isoformat()
text = path.read_text()
text = re.sub(r'^status:.*$', 'status: blocked', text, flags=re.MULTILINE)
text = re.sub(r'^blocked_by:.*$', 'blocked_by: "TASK-007"', text, flags=re.MULTILINE)
text = re.sub(r'^updated_date:.*$', f'updated_date: "{today}"', text, flags=re.MULTILINE)
path.write_text(text)
print("TASK-011 → blocked by TASK-007")
EOF
```

**Complete a task:**

```bash
python3 - << 'EOF'
from pathlib import Path
import re, datetime

path = Path("implementations/B-pure-markdown/tasks/TASK-011.md")
today = datetime.date.today().isoformat()
text = path.read_text()
text = re.sub(r'^status:.*$', 'status: done', text, flags=re.MULTILINE)
text = re.sub(r'^updated_date:.*$', f'updated_date: "{today}"', text, flags=re.MULTILINE)
path.write_text(text)
print("TASK-011 → done")
EOF
```

**Re-score after changing priority or due_date:**

```bash
python3 scripts/score_tasks.py --impl B          # write
python3 scripts/score_tasks.py --impl B --dry-run  # preview only
```

---

### Delete / archive a task

```bash
# Soft-delete: move to flagged/ (stays in git history, out of active queue)
mv implementations/B-pure-markdown/tasks/TASK-011.md \
   implementations/B-pure-markdown/flagged/TASK-011-archived.md

# Hard delete
rm implementations/B-pure-markdown/tasks/TASK-011.md

# Recommended: mark done and leave it (preserves extraction history)
# Then filter it out of daily-brief with the default --status todo,in-progress
```

---

### daily-brief.py reference

```bash
# Default: todo + in-progress, sorted by score, max 20
python3 implementations/B-pure-markdown/daily-brief.py

# Just my tasks
python3 implementations/B-pure-markdown/daily-brief.py --assignee @alice

# Top 5 only
python3 implementations/B-pure-markdown/daily-brief.py --limit 5

# See blocked tasks
python3 implementations/B-pure-markdown/daily-brief.py --status blocked

# Everything (all statuses)
python3 implementations/B-pure-markdown/daily-brief.py --all

# Combine: my in-progress and blocked tasks
python3 implementations/B-pure-markdown/daily-brief.py \
  --assignee @alice --status in-progress,blocked
```

Sample output:
```
============================================================
  DAILY BRIEF — 2026-03-10
  Implementation B (Pure Markdown)
============================================================

  Showing 3 of 10 task(s) | statuses: in-progress, todo

  ○ TASK-007  [@alice]
    Provision Anthropic API key and add to .env file 🟠 DUE IN 2d
    ████░░░░░░ 4.4 MEDIUM

  ○ TASK-011  [@bob]
    Migrate database to Postgres                     (due 2026-03-28)
    ████░░░░░░ 3.6 LOW

  ✗ TASK-008  [@julien]
    Wire ANTHROPIC_API_KEY into score_tasks.py LLM  (due 2026-03-07)
    ████░░░░░░ 3.6 LOW

============================================================
  Summary: 8 todo | 1 in-progress | 1 blocked
============================================================
```

**Icon key:** `○` todo · `◐` in-progress · `◑` review · `●` done · `✗` blocked

---

## Implementation C — Backlog.md

**When to use:** your team wants a visual Kanban board alongside AI agent access, or you're
already using Backlog.md. Tasks live in `implementations/C-backlog-md/backlog/tasks/`.

### Setup

```bash
npm install -g backlog.md

cd implementations/C-backlog-md
backlog init "notes-to-tasks-C" --defaults --agent-instructions none
```

---

### Create a task

**Via backlog CLI:**

```bash
cd implementations/C-backlog-md

# Minimal
backlog task create "Add rate limiting to the API" --plain

# With metadata
backlog task create "Add rate limiting to the API" \
  --assignee alice \
  --labels "backend,api" \
  --description "Extracted from [[2026-03-05-sprint-planning]] | Due: 2026-03-15" \
  --plain
```

Output:
```
File: implementations/C-backlog-md/backlog/tasks/task-11 - Add-rate-limiting-to-the-API.md
```

**Then add score fields:**

```bash
python3 scorer.py          # writes score/urgency/impact/effort to frontmatter
python3 scorer.py --list   # verify priority ranking
```

**From a meeting note:**

```bash
cd implementations/C-backlog-md
python3 importer.py ../../meeting-notes/2026-03-05-sprint-planning.md
python3 scorer.py
```

**Dry-run preview:**

```bash
python3 importer.py ../../meeting-notes/2026-03-05-sprint-planning.md --dry-run
```

---

### Update a task

**Via backlog CLI:**

```bash
cd implementations/C-backlog-md

# Change status
backlog task edit task-11 --status "In Progress"

# View current state
backlog task view task-11 --plain
```

**Edit frontmatter directly** (to add/change score fields or `blocked_by`):

```bash
# Find the file
ls backlog/tasks/ | grep "task-11"
# → task-11 - Add-rate-limiting-to-the-API.md

$EDITOR "backlog/tasks/task-11 - Add-rate-limiting-to-the-API.md"
```

Add to frontmatter:
```yaml
blocked_by: "task-07"
status: To Do   # Backlog.md statuses: "To Do", "In Progress", "Done"
```

**Re-score after edits:**

```bash
python3 scorer.py --dry-run   # preview
python3 scorer.py             # write
```

---

### Delete / archive a task

```bash
cd implementations/C-backlog-md

# Archive via CLI (moves to backlog/archive/)
backlog task archive task-11

# Hard delete
rm "backlog/tasks/task-11 - Add-rate-limiting-to-the-API.md"

# List to confirm
backlog task list --plain
```

---

### Kanban board and MCP

```bash
# Open Kanban in browser (localhost:6420)
backlog board

# List tasks in terminal (no browser)
backlog task list --plain

# MCP server for Claude Code (add to .claude/mcp.json — already done by setup)
backlog mcp start \
  --cwd /absolute/path/to/implementations/C-backlog-md
```

The `.claude/mcp.json` entry (already configured):
```json
{
  "mcpServers": {
    "backlog": {
      "command": "backlog",
      "args": ["mcp", "start", "--cwd", "/path/to/implementations/C-backlog-md"],
      "cwd": "/path/to/implementations/C-backlog-md"
    }
  }
}
```

---

## Vault Insights

The "task vault" is the full set of task files across all implementations — or whichever
implementation you're using as the source of truth. The patterns below show how to ask
meaningful questions of it through the coding harness (Claude Code, Pi, Gemini CLI, etc.)

These are **prompt templates** for use inside your agent session. Paste them as-is or adapt.

---

### What should I work on right now?

**For Implementation B (file-based agents):**

```
Read all files in implementations/B-pure-markdown/tasks/.
Filter to status=todo, no unresolved dependencies (dependencies: []).
Sort by score descending. Show the top 3 with their title, score, assignee, and due_date.
```

**For Implementation A (Claude Code with MCP):**

```
Tool: list_tasks
{ "status": "todo", "min_score": 4.0 }
```

**For Implementation C:**

```bash
python3 implementations/C-backlog-md/scorer.py --list 2>/dev/null | head -15
```

---

### What's blocked and why?

```
Read all task files in implementations/B-pure-markdown/tasks/.
Find every task where status is "blocked".
For each blocked task, show: id, title, assignee, blocked_by field, and the title of the
blocking task (look it up by id).
Format as: TASK-NNN is blocked by TASK-MMM ("<blocking task title>") — assigned to @person
```

Example output a well-functioning agent should produce:
```
TASK-008 is blocked by TASK-007 ("Provision Anthropic API key") — assigned to @julien
```

---

### Who has the most open work?

```
Read all files in implementations/B-pure-markdown/tasks/.
Group todo and in-progress tasks by assignee.
For each assignee show: task count, total score (sum), and their highest-priority task title.
Sort by total score descending.
```

Expected shape of answer:
```
@julien  — 4 tasks, total score 14.8, top: "Wire ANTHROPIC_API_KEY into score_tasks.py"
@alice   — 3 tasks, total score 11.2, top: "Provision Anthropic API key"
@bob     — 3 tasks, total score 10.8, top: "Retry Backlog.md CLI install via npm"
```

---

### What's due this week and who owns it?

```
Read all task files in implementations/B-pure-markdown/tasks/.
Filter to status: todo or in-progress.
Filter to due_date within the next 7 days (today is YYYY-MM-DD).
Sort by due_date ascending. Show id, title, assignee, due_date, score.
Flag any that are overdue (due_date < today).
```

---

### Which labels have the most open work?

```
Read all task files in implementations/B-pure-markdown/tasks/.
Filter to status: todo or in-progress.
Count tasks per label. For each label show the count and the average score of its tasks.
Sort by count descending.
```

Expected shape:
```
testing      — 4 tasks, avg score 3.6
api          — 2 tasks, avg score 4.0
docs         — 2 tasks, avg score 3.6
backend      — 2 tasks, avg score 3.6
```

---

### What got completed recently?

```
Read all task files in implementations/B-pure-markdown/tasks/.
Filter to status: done.
Sort by updated_date descending. Show the last 5 completed tasks with their title,
assignee, and updated_date.
```

---

### Are there any dependency cycles?

```
Read all task files in implementations/B-pure-markdown/tasks/.
Build a directed graph: task A → task B if B appears in A's dependencies list.
Detect any cycles. If found, list the cycle. If none, confirm the graph is acyclic.
```

---

### Summarise what the team shipped from a specific meeting

```
The meeting note is meeting-notes/2026-03-05-sprint-planning.md.
Find all task files whose source field references this meeting note
(look for "2026-03-05-sprint-planning" in the source field).
Show their current status. How many are done, in-progress, todo, blocked?
```

---

### Score a specific task against the rubric

```
Read scripts/prompts/impact_rubric.md and scripts/prompts/effort_rubric.md.
Read implementations/B-pure-markdown/tasks/TASK-007.md.
Apply the impact rubric to this task and give it a score 1-10 with rationale.
Apply the effort rubric and give it a score 1-10 with rationale.
Compute the final score: (urgency × 0.4) + (impact × 0.4) - (effort × 0.2).
Compare to the current heuristic score in the frontmatter.
```

---

### Generate a standup summary

```
Read all task files in implementations/B-pure-markdown/tasks/.
For each assignee, produce a standup bullet:
  - Yesterday: tasks moved to done or in-progress in the last 24 hours (updated_date = today)
  - Today: highest-score todo task for that person
  - Blockers: any of their tasks with status=blocked

Format as Slack-ready markdown.
```

Example output:
```
*@alice*
• Yesterday: started TASK-007 (Provision API key)
• Today: TASK-004 – Write 5 tasks via MCP tool calls [score 3.6]
• Blockers: none

*@julien*
• Yesterday: —
• Today: TASK-008 – Wire ANTHROPIC_API_KEY into score_tasks.py [score 3.6]
• Blockers: TASK-008 blocked by TASK-007
```

---

### Find tasks that should be split

```
Read all task files in implementations/B-pure-markdown/tasks/.
Flag any task where effort ≥ 8 and status is todo or in-progress.
For each flagged task, suggest 2-3 smaller sub-tasks that together cover the original scope.
Output as a proposed TASK-NNN breakdown.
```

---

### Cross-implementation audit

```
Compare the task stores across all three implementations:
  A: implementations/A-mcp-server/tasks/
  B: implementations/B-pure-markdown/tasks/
  C: implementations/C-backlog-md/backlog/tasks/

For each implementation, report:
  - Total task count
  - Count by status
  - Average score
  - Any tasks present in B but missing from A or C (by title match)
```

---

## Quick reference

| Action | Impl A (MCP) | Impl B (Markdown) | Impl C (Backlog.md) |
|---|---|---|---|
| Create | `create_task` tool | write `TASK-NNN.md` | `backlog task create` |
| Read all | `list_tasks {}` | `daily-brief.py` | `backlog task list --plain` |
| Filter by assignee | `list_tasks {"assignee":"@x"}` | `daily-brief.py --assignee @x` | `backlog task list --plain` + grep |
| Filter by score | `list_tasks {"min_score":7}` | `daily-brief.py` (sorted) | `scorer.py --list` |
| Update status | `update_task {"id":"…","status":"…"}` | edit frontmatter | `backlog task edit` |
| Complete | `complete_task {"id":"…"}` | set `status: done` | `backlog task edit --status Done` |
| Delete/archive | `mv` to `flagged/` | `mv` to `flagged/` | `backlog task archive` |
| Score | `score_tasks {}` | `score_tasks.py --impl B` | `scorer.py` |
| Extract from note | `extract_tasks.py --impl A` | `extract_tasks.py --impl B` | `importer.py` |
