#!/usr/bin/env python3
"""
extract_tasks.py — Meeting note → structured task files

Usage:
    python3 scripts/extract_tasks.py meeting-notes/2026-02-26-team-sync.md
    python3 scripts/extract_tasks.py meeting-notes/2026-02-26-team-sync.md --impl B
    python3 scripts/extract_tasks.py meeting-notes/2026-02-26-team-sync.md --dry-run
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = REPO_ROOT / "scripts" / "prompts"

IMPL_TASK_DIRS = {
    "A": REPO_ROOT / "implementations" / "A-mcp-server" / "tasks",
    "B": REPO_ROOT / "implementations" / "B-pure-markdown" / "tasks",
    # C is managed by Backlog.md CLI; extraction writes to a staging dir
    "C": REPO_ROOT / "implementations" / "C-backlog-md" / "backlog",
}

FLAGGED_DIR = REPO_ROOT / "flagged"
CONFIDENCE_THRESHOLD = 0.7

# Keywords that increase urgency score
URGENCY_KEYWORDS = {
    "blocking": 3, "blocked": 3, "critical": 3, "p0": 3,
    "asap": 2, "urgent": 2, "immediately": 2, "eod": 2, "end of day": 2, "p1": 2,
    "high priority": 1, "soon": 1,
}


def parse_args():
    parser = argparse.ArgumentParser(description="Extract tasks from a meeting note")
    parser.add_argument("note", type=Path, help="Path to meeting note markdown file")
    parser.add_argument("--impl", choices=["A", "B", "C"], default="B",
                        help="Target implementation (default: B)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print extracted tasks without writing files")
    return parser.parse_args()


def read_note(path: Path) -> str:
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def extract_action_items(text: str) -> list[dict]:
    """
    Parse action items from the ## Action Items section.
    Expected format: `- [ ] **@owner** — description — due date`
    Returns list of raw action item dicts.
    """
    items = []
    in_section = False

    for line in text.splitlines():
        if re.match(r"^##\s+Action Items", line, re.IGNORECASE):
            in_section = True
            continue
        if in_section and re.match(r"^##\s+", line):
            break
        if not in_section:
            continue

        # Match checkbox action items
        m = re.match(r"^\s*-\s+\[[ x]\]\s+(.+)$", line, re.IGNORECASE)
        if not m:
            continue

        raw = m.group(1).strip()
        items.append({"raw": raw, "line": line.strip()})

    return items


def parse_action_item(raw: str, source_file: str) -> dict:
    """
    Parse a raw action item string into structured task fields.
    Heuristic parsing — LLM integration point for production use.
    """
    # Extract owner
    owner_match = re.search(r"\*\*(@\w+)\*\*", raw)
    assignee = owner_match.group(1) if owner_match else "unassigned"

    # Extract due date
    due_match = re.search(
        r"due\s+(\d{4}-\d{2}-\d{2}|next meeting|eod|today|[\w\s]+\d+)",
        raw, re.IGNORECASE
    )
    due_date = due_match.group(1) if due_match else None

    # Extract title (strip owner, due date, meta)
    title = re.sub(r"\*\*@\w+\*\*\s*[—-]\s*", "", raw)
    title = re.sub(r"\s*[—-]\s*due\s+.+", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*[—-]\s*(blocking|depends on|blocked)\s+.+", "", title, flags=re.IGNORECASE)
    title = title.strip(" —-")

    # Detect labels from keywords
    labels = []
    lower = raw.lower()
    for keyword, label in [("auth", "auth"), ("api", "api"), ("db", "database"),
                            ("database", "database"), ("test", "testing"),
                            ("deploy", "deploy"), ("bug", "bug"), ("fix", "bug"),
                            ("doc", "docs"), ("design", "design"), ("front", "frontend"),
                            ("back", "backend"), ("infra", "infrastructure")]:
        if keyword in lower:
            labels.append(label)

    # Compute confidence based on how much structured info we found
    confidence = 0.5
    if owner_match:
        confidence += 0.2
    if due_date:
        confidence += 0.15
    if len(title) > 10:
        confidence += 0.15

    # Urgency from keywords — accumulate all matches
    urgency = 5
    for kw, boost in URGENCY_KEYWORDS.items():
        if kw in lower:
            urgency = min(10, urgency + boost)

    source_stem = Path(source_file).stem
    wikilink = f"[[{source_stem}]]"

    return {
        "title": title,
        "status": "todo",
        "assignee": assignee,
        "priority": "high" if urgency >= 8 else "medium" if urgency >= 5 else "low",
        "urgency": urgency,
        "impact": None,   # requires LLM scoring
        "effort": None,   # requires LLM scoring
        "score": None,    # computed after LLM scoring
        "due_date": due_date,
        "labels": list(set(labels)),
        "dependencies": [],
        "source": wikilink,
        "confidence": round(confidence, 2),
    }


def next_task_id(task_dir: Path) -> str:
    existing = list(task_dir.glob("TASK-*.md")) + list(FLAGGED_DIR.glob("TASK-*.md"))
    if not existing:
        return "TASK-001"
    nums = []
    for f in existing:
        m = re.match(r"TASK-(\d+)", f.stem)
        if m:
            nums.append(int(m.group(1)))
    return f"TASK-{(max(nums) + 1):03d}" if nums else "TASK-001"


def render_task_md(task_id: str, fields: dict, today: str) -> str:
    labels_yaml = json.dumps(fields.get("labels") or [])
    deps_yaml = json.dumps(fields.get("dependencies") or [])
    due = fields.get("due_date") or "null"

    return f"""---
id: {task_id}
title: "{fields['title']}"
status: {fields['status']}
assignee: "{fields['assignee']}"
priority: {fields['priority']}
score: null
urgency: {fields['urgency']}
impact: null
effort: null
created_date: "{today}"
updated_date: "{today}"
due_date: "{due}"
labels: {labels_yaml}
dependencies: {deps_yaml}
source: "{fields['source']}"
confidence: {fields['confidence']}
---

# {fields['title']}

> Extracted from {fields['source']}. Run `python3 scripts/score_tasks.py` to compute final score.

## Context

<!-- Add context from the meeting note here -->

## Acceptance criteria

<!-- What does done look like? -->

## Notes

<!-- Implementation notes, links, references -->
"""


def write_task(task_id: str, content: str, destination: Path, dry_run: bool) -> Path:
    filepath = destination / f"{task_id}.md"
    if dry_run:
        print(f"\n{'='*60}")
        print(f"[DRY RUN] Would write: {filepath}")
        print(content)
    else:
        destination.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        print(f"  Written: {filepath}")
    return filepath


def main():
    args = parse_args()
    note_text = read_note(args.note)
    today = date.today().isoformat()
    task_dir = IMPL_TASK_DIRS[args.impl]

    raw_items = extract_action_items(note_text)
    if not raw_items:
        print("No action items found in ## Action Items section.")
        print("Check that your meeting note uses the TEMPLATE.md format.")
        sys.exit(0)

    print(f"Found {len(raw_items)} action item(s) in {args.note.name}")
    print(f"Target: Implementation {args.impl} ({task_dir})")
    print(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")

    written, flagged_count = 0, 0

    for item in raw_items:
        fields = parse_action_item(item["raw"], str(args.note))
        task_id = next_task_id(task_dir)
        content = render_task_md(task_id, fields, today)

        if fields["confidence"] < CONFIDENCE_THRESHOLD:
            dest = FLAGGED_DIR
            label = f"  [FLAGGED confidence={fields['confidence']}]"
            flagged_count += 1
        else:
            dest = task_dir
            label = f"  [OK confidence={fields['confidence']}]"
            written += 1

        print(f"\n{task_id}: {fields['title'][:60]}")
        print(label)
        write_task(task_id, content, dest, args.dry_run)

    print(f"\nDone: {written} task(s) written, {flagged_count} flagged for review")
    if flagged_count:
        print(f"Review flagged tasks in: {FLAGGED_DIR}")
    if not args.dry_run and written:
        print("\nNext step: python3 scripts/score_tasks.py")


if __name__ == "__main__":
    main()
