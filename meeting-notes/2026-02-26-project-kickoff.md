# Meeting: notes-to-tasks Project Kickoff

**Date:** 2026-02-26
**Attendees:** @julien, @alice, @bob
**Facilitator:** @julien
**Note-taker:** @alice

---

## Agenda

1. Agree on repo structure and three-architecture approach
2. Assign owners for each implementation
3. Define scoring formula and schema
4. Set timeline for evaluation

---

## Discussion

### Repo structure and architecture choice

We aligned on the three-parallel-implementation approach described in the README. The goal is not
to pick a winner up front, but to build all three and let the evaluation data decide. Each
implementation shares the same SCHEMA.md spec, extraction scripts, and meeting notes store.

@bob raised a concern that Implementation C (Backlog.md) adds a hard dependency on a third-party
CLI. We agreed to document this prominently in C's README and evaluation matrix.

### Scoring formula

Agreed on: `score = (urgency × 0.4) + (impact × 0.4) - (effort × 0.2)`

The asymmetry is intentional — effort is a tiebreaker, not a primary driver. A high-impact
urgent task that is hard should still rank above a low-impact easy task.

### Timeline

- Week 1: shared foundation (SCHEMA, scripts, templates) ← blocking everything else
- Week 2: all three implementations running end-to-end
- Week 3: evaluation + comparison matrix filled in

---

## Action Items

- [ ] **@alice** — Set up Python virtualenv and verify extract_tasks.py works on the kickoff note — due 2026-02-28
- [ ] **@bob** — Install Backlog.md CLI and test importer.py against a sample task — due 2026-02-28
- [ ] **@julien** — Add ANTHROPIC_API_KEY to repo secrets and implement LLM scoring in score_tasks.py — due 2026-03-04
- [ ] **@alice** — Write 5 tasks via MCP tool calls and verify list_tasks filters work — due 2026-03-04
- [ ] **@bob** — Fill in docs/EVALUATION.md columns for Implementation C after testing — due 2026-03-07
- [ ] **@julien** — Create sample meeting note for end-to-end pipeline testing — due 2026-02-27

---

## Decisions

- Use `python3` (not `python`) in all scripts and READMEs — macOS ships without `python` alias
- Implementation B (pure markdown) is the default for agents without MCP support
- `confidence < 0.7` tasks always go to `flagged/` — no exceptions

---

## Follow-ups / Parking Lot

- Evaluate syncing Implementation A tasks to GitHub Issues via the official GitHub MCP server
- Consider adding a `blocked_by` validation step to `score_tasks.py`

---

## Next meeting

**Date:** 2026-03-05
**Agenda items to carry forward:**
- [ ] Review evaluation matrix first pass
- [ ] Decide on LLM provider for production scoring
