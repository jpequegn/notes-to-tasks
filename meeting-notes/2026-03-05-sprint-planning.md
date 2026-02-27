# Meeting: Sprint Planning — Week of March 9

**Date:** 2026-03-05
**Attendees:** @julien, @alice, @bob
**Facilitator:** @julien
**Note-taker:** @bob

---

## Agenda

1. Review evaluation status for all three implementations
2. Unblock LLM scoring
3. Plan sprint goals

---

## Discussion

### Evaluation status

Implementation B is running well — daily-brief.py gives a clean priority view. A and C need
more validation. The main blocker across all three is LLM scoring: without ANTHROPIC_API_KEY,
all impact/effort values fall back to heuristics, which makes all tasks cluster around 3.6.

### LLM scoring blocker

@alice confirmed she can get an Anthropic API key by EOD today. Once unblocked, @julien will
wire it into score_tasks.py. This is blocking the evaluation because without score variance
we can't meaningfully compare implementations.

### Backlog.md CLI

@bob hasn't been able to install Backlog.md CLI on the M2 Mac — there's a known ARM build issue.
He'll try the npm fallback: `npm install -g backlog.md`. If that doesn't work by Friday, we
pivot to skipping C's Kanban UI and evaluating it purely through the importer/scorer scripts.

---

## Action Items

- [ ] **@alice** — Provision Anthropic API key and add to .env file — due 2026-03-05 — blocking LLM scoring
- [ ] **@julien** — Wire ANTHROPIC_API_KEY into score_tasks.py LLM path — due 2026-03-07 — depends on @alice's key
- [ ] **@bob** — Retry Backlog.md CLI install via npm and document result in C's README — due 2026-03-06
- [ ] **@julien** — Run full evaluation matrix with real LLM scores and fill in docs/EVALUATION.md — due 2026-03-10
- [ ] we should probably improve the daily-brief output at some point

---

## Decisions

- If Backlog.md CLI ARM issue is unresolved by 2026-03-08, evaluate C without the Kanban UI
- LLM scoring will use Claude claude-haiku-3-5 for cost efficiency (not Sonnet)
- `.env` file is gitignored — each developer manages their own API keys locally

---

## Follow-ups / Parking Lot

- Consider adding a `--since` flag to daily-brief.py to filter tasks created after a date
- Open question: should `blocked` tasks appear in the daily brief at all?

---

## Next meeting

**Date:** 2026-03-12
**Agenda items to carry forward:**
- [ ] Final evaluation results
- [ ] Pick winning implementation
