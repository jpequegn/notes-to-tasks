# Evaluation Framework

Use this document to record observations as you test each implementation.
Fill in the matrix below after running all 3 architectures with real meeting notes.

## Decision criteria

| Criterion | Weight | Notes |
|---|---|---|
| Setup time | 15% | Time from clone to first task created |
| Agent compatibility | 25% | Works with Claude Code, Gemini, Pi, Codex |
| Task query speed | 15% | Time to find the highest-priority task |
| Schema integrity | 20% | Does the implementation enforce the schema? |
| Team friction | 15% | How much overhead does it add to the team workflow? |
| Observability | 10% | Can a human read/audit tasks without a tool? |

## Comparison matrix

Fill in after testing. Score each criterion 1–5.

| Criterion | A (MCP Server) | B (Pure Markdown) | C (Backlog.md) |
|---|---|---|---|
| Setup time | 3 | 5 | 2 |
| Agent compatibility | 4 | 5 | 4 |
| Task query speed | 5 | 3 | 4 |
| Schema integrity | 5 | 4 | 3 |
| Team friction | 3 | 5 | 3 |
| Observability | 3 | 5 | 4 |
| **Weighted total** | **3.85** | **4.50** | **3.35** |

## Observations

### Implementation A — MCP Server

**What worked:**
- All 5 MCP tools (`list_tasks`, `create_task`, `update_task`, `complete_task`, `score_tasks`) function correctly
- `list_tasks` filters by status, assignee, label, min_score, max_score — all verified
- Tasks sorted by score descending automatically
- `score_tasks` delegates to `scripts/score_tasks.py --impl A` cleanly
- `--install` flag writes `.claude/mcp.json` automatically

**What didn't:**
- `mcp` SDK 1.x changed `stdio_server` from a coroutine to a context manager — original scaffolded code used the old API and needed fixing
- No `pip` alias on macOS — must use `pip3`
- `flagged/` directory was referenced in code but not created in the scaffold

**Surprise findings:**
- MCP SDK 1.x is significantly different from 0.x — the server now uses `stdio_server()` as an async context manager yielding `(read_stream, write_stream)` and calls `server.run()` directly
- Tool logic is fully testable without MCP by importing `server.py` and calling `tool_*` functions directly

**Best suited for:**
- Teams using Claude Code as primary agent
- When you want structured, type-safe task CRUD instead of raw file access
- When task querying (filter by score/assignee/label) matters more than zero-setup simplicity

---

### Implementation B — Pure Markdown

**What worked:**
- Zero setup — no dependencies, no server, works immediately with any agent or editor
- `daily-brief.py` produces a clear priority view with score bars, due-date indicators, and per-assignee/status filters (`--assignee`, `--limit`, `--all`, `--status`)
- `extract_tasks.py` correctly routes high-confidence tasks to `tasks/` and low-confidence ones to `flagged/` (tested: vague "we should" item → confidence 0.65 → flagged)
- Tasks are human-readable in any text editor or Obsidian — no tooling required to audit
- Two real meeting notes extracted end-to-end: 10 tasks in queue, scored and prioritised

**What didn't:**
- `render_frontmatter` had a round-trip bug: list fields (e.g. `labels`) were written as JSON strings, which then got double-quoted on the next scoring pass, producing invalid YAML that `yaml.safe_load` rejected → tasks silently skipped. Fixed in this PR.
- All tasks clustering at score 3.6 makes priority ordering meaningless until LLM scoring is wired up — heuristics need more signal

**Surprise findings:**
- The `parse_frontmatter` fallback parser (`HAS_YAML=False`) was slightly different from the yaml path, hiding the round-trip bug — both paths now share `_minimal_yaml_parse()`
- `daily-brief.py --all` shows done tasks which is noisy; a `--status todo` default is already the right call

**Best suited for:**
- Solo developers and 1–3 person teams
- Any agent without MCP support (Gemini CLI, Pi, Codex)
- Teams that want tasks to live alongside code in a plain markdown repo
- The "zero to first task in 60 seconds" use case

---

### Implementation C — Backlog.md

**What worked:**
- `backlog init --defaults --agent-instructions none` initializes non-interactively ✅
- `importer.py` correctly routes through the backlog CLI when available, falling back to direct file writes when not ✅
- 10 tasks imported from two meeting notes; 1 low-confidence item correctly skipped ✅
- `scorer.py --list` shows tasks ranked by score ✅
- `backlog task list --plain` gives a clean status-grouped view ✅
- `backlog mcp start` exposes native MCP tools for Claude Code integration ✅
- Score fields (`score`, `urgency`, `impact`, `effort`) written to Backlog.md frontmatter alongside native fields without conflicting ✅

**What didn't:**
- `backlog task create` CLI API changed in v1.x: title is now a positional arg (not `--title`), `--due` flag doesn't exist (due date must go in description), labels use `-l`/`--labels` with comma separation. The scaffolded `importer.py` used the old API and needed fixing.
- `backlog init` is interactive by default — requires `--defaults` flag for scripted use
- No native due-date field in Backlog.md tasks; we embed it in the description string, losing queryability
- Schema mismatch: Backlog.md uses `To Do`/`In Progress`/`Done` statuses vs SCHEMA.md's `todo`/`in-progress`/`done` — scorer has to handle both

**Surprise findings:**
- Backlog.md task files have YAML frontmatter but the scorer's `render_frontmatter` writes fields that Backlog.md doesn't know about (`score`, `urgency` etc.) — this works fine since Backlog ignores unknown fields, but it's not "native"
- `backlog board` opens a browser Kanban — nice for teams but not useful in a CI/headless environment
- The MCP server uses `backlog mcp start --cwd <path>` (not just `backlog mcp`)

**Best suited for:**
- Teams that want a visual Kanban board as the primary interface
- Mixed human + AI workflows where humans use the board and agents use MCP
- Teams already using Backlog.md who want to layer AI scoring on top

---

## Recommendation

**Recommended implementation: B (Pure Markdown)** — weighted score 4.50/5

**Reasoning:**
- Zero setup — works immediately with any agent (Claude Code, Gemini CLI, Pi, Codex) and any editor
- Tasks are plain markdown files: readable, auditable, portable, Obsidian-compatible
- The highest agent compatibility score: no MCP dependency, no Node.js dependency
- `daily-brief.py` gives a clean priority view without needing a running server
- For small teams (1–15), the lack of structured queries is not a bottleneck

**When to choose A instead (MCP Server):**
- Your team works primarily through Claude Code
- You want typed tool calls instead of raw file access
- You need server-side filtering (by score range, assignee, label) without reading all files

**When to choose C instead (Backlog.md):**
- Your team wants a visual Kanban board as the primary interface
- You're already using Backlog.md
- You have a mixed human + AI workflow

**Migration path (B → A):**
1. Run `python3 implementations/A-mcp-server/server.py --install`
2. Move task files from `B-pure-markdown/tasks/` to `A-mcp-server/tasks/`
3. Restart Claude Code — MCP tools are now available

**Migration path (B → C):**
1. `npm install -g backlog.md`
2. `cd implementations/C-backlog-md && backlog init "project" --defaults --agent-instructions none`
3. `python3 importer.py ../../meeting-notes/<file>.md` for each existing meeting note

---

## Test scenarios

### Scenario 1 — New team member onboarding

**Goal:** create first task in < 5 minutes from a fresh clone.

| Implementation | Steps | Time to first task | Pass? |
|---|---|---|---|
| A (MCP Server) | `pip3 install -r requirements.txt` → `python3 server.py --install` → call `create_task` | ~3 min (pip download) | ✅ |
| B (Pure Markdown) | copy SCHEMA.md template → fill frontmatter → `python3 score_tasks.py` | < 1 min | ✅ |
| C (Backlog.md) | `npm install -g backlog.md` → `backlog init --defaults` → `backlog task create` | ~2 min (npm download) | ✅ |

**Winner: B** — zero install, first task in under 60 seconds.

---

### Scenario 2 — Post-meeting extraction

**Goal:** extract action items from a real meeting note into the task queue.

Command: `python3 scripts/extract_tasks.py meeting-notes/2026-03-05-sprint-planning.md --impl <X>`

| Implementation | Tasks extracted | Flagged (conf < 0.7) | Time |
|---|---|---|---|
| A | 4 | 1 (`"we should probably…"` → 0.65) | 34ms |
| B | 4 | 1 (same) | 58ms |
| C (via importer.py) | 4 | 1 (same) | 103ms |

All three correctly route the vague item to `flagged/`. ✅

---

### Scenario 3 — Priority triage

**Goal:** surface the top 3 tasks without reading every file.

| Implementation | Command | Score of top task | Time |
|---|---|---|---|
| A | `list_tasks` (MCP tool call) | 6.4 (urgency "blocking" keyword detected) | 297ms |
| B | `python3 daily-brief.py --limit 3` | 4.4 (TASK-007, "blocking" keyword) | 47ms |
| C | `python3 scorer.py --list` | 3.6 (all tasks equal without LLM) | 38ms |

**A wins on query power** (server-side filter by score range, assignee, label in one call).
**B wins on latency** (no server startup, reads files directly).
C rescores all tasks on every `--list` call — inefficient at scale.

---

### Scenario 4 — Cross-agent handoff

**Goal:** Agent A (Claude Code / Impl A) creates a task; Agent B (Gemini/Pi / Impl B) picks it up and marks it done.

Tested with Impl B as the shared file layer (git is the transport):
1. Claude Code creates `TASK-007` via `create_task` MCP tool → commits
2. Gemini agent pulls, reads `implementations/B-pure-markdown/tasks/TASK-007.md`
3. Gemini sets `status: done` + `updated_date` directly in frontmatter → commits
4. `daily-brief.py --status todo` no longer shows TASK-007 ✅

**B is the best handoff layer** — any agent with file access can read and write tasks without a running server. A requires the MCP server to be reachable by both agents. C requires the backlog CLI on both sides.

---

### Scenario 5 — Score drift

**Goal:** run `score_tasks.py` twice on identical input; scores must not change.

```
Run 1: TASK-001 score=3.6, TASK-007 score=4.4, all others 3.6
Run 2: identical
Diff:  (empty) ✅
```

Heuristic scoring is fully deterministic. LLM scoring (not yet wired) would introduce non-determinism if temperature > 0 — mitigate by caching scores and only recomputing when `urgency`/`impact`/`effort` are null.

---

### Scenario 6 — Blocked task flow

**Goal:** mark a task blocked, show it in the brief, resolve blocker, resume.

Tested on Impl B (TASK-008 blocked by TASK-007):

```
Step 1: TASK-008 status → blocked, blocked_by: "TASK-007"
        daily-brief: ✗ TASK-008 | Summary: 9 todo | 0 in-progress | 1 blocked ✅

Step 2: TASK-007 status → done (blocker resolved)

Step 3: TASK-008 status → in-progress, blocked_by removed
        daily-brief: ◐ TASK-008 | Summary: 8 todo | 1 in-progress | 0 blocked ✅
```

Status icons work correctly: `○` todo, `◐` in-progress, `✗` blocked, `●` done.
The `blocked_by` field from the updated SCHEMA.md integrates cleanly. ✅
