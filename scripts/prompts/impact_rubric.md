# Impact Scoring Rubric

Score the impact of a task on a scale of 1–10 using the criteria below.

## Input

Task title: {title}
Task context: {context}
Labels: {labels}
Source meeting: {source}

## Rubric

| Score | Description |
|---|---|
| 9–10 | Directly affects revenue, production stability, or a large number of users. Blocking major features or causing customer-facing issues. |
| 7–8 | Significant business value. Enables a key feature, improves core user experience, or unblocks other team members. |
| 5–6 | Meaningful improvement. Improves developer experience, reduces tech debt, or adds useful functionality. |
| 3–4 | Nice-to-have. Minor improvement, cleanup, or documentation with limited immediate effect. |
| 1–2 | Negligible impact. Cosmetic change, trivial task, or already superseded by other work. |

## Output format

Return only a JSON object:
```json
{"impact": <integer 1-10>, "rationale": "<one sentence>"}
```
