# Task Schema

Canonical frontmatter spec shared across all implementations.

## Frontmatter

```yaml
---
id: TASK-001
title: "Implement auth middleware"
status: todo | in-progress | review | done | blocked
assignee: "@username | unassigned"
priority: critical | high | medium | low
score: 7.8                          # computed by scoring engine
urgency: 8                          # 1-10, rule-based (keywords + deadline proximity)
impact: 9                           # 1-10, LLM-scored with rubric
effort: 3                           # 1-10, LLM-scored with rubric
created_date: "2026-02-23"
updated_date: "2026-02-23"
due_date: "2026-03-01"              # or null
labels: ["backend", "auth"]
dependencies: ["TASK-000"]
blocked_by: null                    # task id or external dep string; required when status=blocked
source: "[[2026-02-23 Team Sync]]"  # wikilink back to meeting note
confidence: 0.85                    # extraction confidence; tasks < 0.7 flagged for review
---
```

## Scoring

**Formula:** `score = (urgency × 0.4) + (impact × 0.4) - (effort × 0.2)`

| Field | Method | Rationale |
|---|---|---|
| `urgency` | Rule-based | Deadline proximity + keywords ("blocking", "ASAP", "critical") |
| `impact` | LLM-scored | Rubric: business value, number of people affected, strategic alignment |
| `effort` | LLM-scored | Rubric: hours estimate, complexity, unknowns |
| `score` | Computed | Final priority ranking |

## Safety gate

Tasks extracted with `confidence < 0.7` are written to a `flagged/` directory and require human
review before being promoted to the main task queue.

## Status transitions

```
todo → in-progress → review → done
              ↓
           blocked → in-progress
```

`blocked` tasks must have a `blocked_by` field referencing the blocking task or external dependency.

## Field constraints

- `id`: Auto-assigned, format `TASK-NNN`, never reused
- `score`: Recomputed on every `score_tasks.py` run; never manually set
- `labels`: Lowercase, hyphen-separated, from the project label taxonomy
- `blocked_by`: Required (non-null) when `status: blocked`; omit or set to `null` otherwise
- `source`: Must reference an existing file in `meeting-notes/`
