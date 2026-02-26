# Task Extraction Prompt

Extract structured action items from a meeting note.

## Input

Meeting note content:
{meeting_note_content}

## Instructions

1. Find all action items — explicit (checkbox lists, "Action items" section) and implicit
   (commitments made during discussion, "we should", "someone needs to", "let's make sure").
2. For each action item, extract:
   - **owner**: who is responsible (@username or "unassigned")
   - **title**: clear, imperative description of what needs to happen (start with a verb)
   - **due_date**: YYYY-MM-DD if mentioned, otherwise null
   - **context**: 1–2 sentence summary of why this matters
   - **labels**: relevant labels from [backend, frontend, api, database, auth, testing, deploy,
     docs, design, infrastructure, bug, research]
   - **confidence**: 0.0–1.0 — how confident you are this is a real, actionable task
     (0.9+ = explicit checkbox; 0.7+ = clearly stated; <0.7 = inferred/ambiguous)
3. Skip vague statements that aren't real tasks ("we should think about X someday").
4. If confidence < 0.7, still include the item but flag it.

## Output format

Return a JSON array:
```json
[
  {
    "title": "Implement OAuth2 login with Google",
    "owner": "@alice",
    "due_date": "2026-03-01",
    "context": "Needed before the Q1 launch. Currently users can only log in with email.",
    "labels": ["auth", "backend"],
    "confidence": 0.92
  }
]
```
