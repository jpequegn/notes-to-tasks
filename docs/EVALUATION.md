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

Run each implementation through these scenarios and record results above:

1. **New team member onboarding** — can they create their first task in < 5 minutes?
2. **Post-meeting extraction** — extract tasks from `meeting-notes/TEMPLATE.md` sample
3. **Priority triage** — find the top 3 tasks to do today, without reading all files
4. **Cross-agent handoff** — Claude Code creates a task, Gemini CLI picks it up and completes it
5. **Score drift** — run `score_tasks.py` twice on the same data, compare results
6. **Blocked task flow** — mark a task blocked, resolve the blocker, resume work
