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
| Setup time | 3 | 5 | |
| Agent compatibility | 4 | 5 | |
| Task query speed | 5 | 3 | |
| Schema integrity | 5 | 4 | |
| Team friction | 3 | 5 | |
| Observability | 3 | 5 | |
| **Weighted total** | **3.85** | **4.50** | |

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

**What didn't:**

**Surprise findings:**

**Best suited for:**

---

## Recommendation

_Fill in after completing evaluation._

**Recommended implementation:**

**Reasoning:**

**Migration path (if switching from B to A or C):**

---

## Test scenarios

Run each implementation through these scenarios and record results above:

1. **New team member onboarding** — can they create their first task in < 5 minutes?
2. **Post-meeting extraction** — extract tasks from `meeting-notes/TEMPLATE.md` sample
3. **Priority triage** — find the top 3 tasks to do today, without reading all files
4. **Cross-agent handoff** — Claude Code creates a task, Gemini CLI picks it up and completes it
5. **Score drift** — run `score_tasks.py` twice on the same data, compare results
6. **Blocked task flow** — mark a task blocked, resolve the blocker, resume work
