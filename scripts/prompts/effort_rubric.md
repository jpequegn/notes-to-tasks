# Effort Scoring Rubric

Score the effort required for a task on a scale of 1–10.
Higher effort = more work = lower final priority score.

## Input

Task title: {title}
Task context: {context}
Labels: {labels}
Source meeting: {source}

## Rubric

| Score | Approximate hours | Description |
|---|---|---|
| 9–10 | > 2 weeks | Major refactor, new architecture, or deeply uncertain. Multiple unknowns. |
| 7–8 | 3–10 days | Significant feature, cross-cutting change, or requires substantial research. |
| 5–6 | 1–3 days | Moderate task. Requires design thinking but scope is clear. |
| 3–4 | 2–8 hours | Well-defined task with clear implementation path. |
| 1–2 | < 2 hours | Trivial: config change, one-liner fix, documentation update. |

## Output format

Return only a JSON object:
```json
{"effort": <integer 1-10>, "rationale": "<one sentence>"}
```
