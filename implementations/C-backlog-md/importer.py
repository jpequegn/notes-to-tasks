#!/usr/bin/env python3
"""
importer.py — Meeting note → Backlog.md task pipeline

Reads a meeting note, extracts action items (reusing the shared extraction logic),
and creates tasks in Backlog.md format under backlog/

Usage:
    python importer.py ../../meeting-notes/2026-02-26-team-sync.md
    python importer.py ../../meeting-notes/2026-02-26-team-sync.md --dry-run
"""

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

IMPL_DIR = Path(__file__).parent
REPO_ROOT = IMPL_DIR.parent.parent
BACKLOG_DIR = IMPL_DIR / "backlog"

# Reuse extraction logic from shared scripts
sys.path.insert(0, str(REPO_ROOT / "scripts"))
try:
    from extract_tasks import extract_action_items, parse_action_item
    HAS_EXTRACT = True
except ImportError:
    HAS_EXTRACT = False


def parse_args():
    parser = argparse.ArgumentParser(description="Import meeting note tasks into Backlog.md")
    parser.add_argument("note", type=Path, help="Path to meeting note")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    return parser.parse_args()


def backlog_cli_available() -> bool:
    try:
        result = subprocess.run(["backlog", "--version"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def create_backlog_task(title: str, assignee: str, due_date: str | None,
                        labels: list, source: str, dry_run: bool) -> bool:
    """Create a task using the backlog CLI."""
    cmd = ["backlog", "task", "create", "--title", title]

    if assignee and assignee != "unassigned":
        cmd += ["--assignee", assignee.lstrip("@")]
    if due_date and due_date not in ("null", None, ""):
        cmd += ["--due", str(due_date)]
    if labels:
        for label in labels:
            cmd += ["--label", label]

    # Add source as a note in the description
    description = f"Extracted from {source}"
    cmd += ["--description", description]

    if dry_run:
        print(f"  [DRY RUN] Would run: {' '.join(cmd)}")
        return True

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(IMPL_DIR))
    if result.returncode != 0:
        print(f"  Error: {result.stderr.strip()}")
        return False
    print(f"  Created: {result.stdout.strip()}")
    return True


def write_backlog_md_directly(title: str, assignee: str, due_date: str | None,
                               labels: list, source: str, task_num: int, dry_run: bool):
    """Fallback: write Backlog.md format directly if CLI is unavailable."""
    BACKLOG_DIR.mkdir(parents=True, exist_ok=True)
    tasks_dir = BACKLOG_DIR / "tasks"
    tasks_dir.mkdir(exist_ok=True)

    today = date.today().isoformat()
    labels_str = ", ".join(labels) if labels else ""
    due_str = str(due_date) if due_date and due_date not in ("null", None) else ""

    content = f"""---
title: "{title}"
status: todo
assignee: "{assignee}"
created: "{today}"
due: "{due_str}"
labels: [{", ".join(f'"{l}"' for l in labels)}]
score: null
urgency: null
impact: null
effort: null
source: "{source}"
---

# {title}

> Imported from {source} on {today}

## Description

## Acceptance criteria

## Notes
"""

    filename = f"task-{task_num:03d}.md"
    path = tasks_dir / filename

    if dry_run:
        print(f"  [DRY RUN] Would write: {path}")
        print(f"  Title: {title}")
        print(f"  Assignee: {assignee} | Due: {due_str} | Labels: {labels_str}")
    else:
        path.write_text(content, encoding="utf-8")
        print(f"  Written: {path}")


def main():
    args = parse_args()

    if not args.note.exists():
        print(f"Error: file not found: {args.note}")
        sys.exit(1)

    if not HAS_EXTRACT:
        print("Error: could not import extract_tasks from scripts/")
        print("Make sure you're running from the repo root or that scripts/ exists.")
        sys.exit(1)

    note_text = args.note.read_text(encoding="utf-8")
    raw_items = extract_action_items(note_text)

    if not raw_items:
        print("No action items found in ## Action Items section.")
        sys.exit(0)

    print(f"Found {len(raw_items)} action item(s) in {args.note.name}")

    use_cli = backlog_cli_available()
    if use_cli:
        print("Using: backlog CLI")
    else:
        print("Note: backlog CLI not found — writing files directly")
        print("Install with: npm install -g backlog.md")

    written, flagged = 0, 0
    existing_tasks = list(BACKLOG_DIR.glob("tasks/task-*.md")) if BACKLOG_DIR.exists() else []
    task_num = len(existing_tasks) + 1

    for item in raw_items:
        fields = parse_action_item(item["raw"], str(args.note))
        source_stem = args.note.stem
        source = f"[[{source_stem}]]"

        print(f"\n→ {fields['title'][:60]}")
        print(f"  confidence={fields['confidence']} assignee={fields['assignee']}")

        if fields["confidence"] < 0.7:
            print(f"  [SKIPPED — confidence < 0.7, review manually]")
            flagged += 1
            continue

        if use_cli:
            success = create_backlog_task(
                title=fields["title"],
                assignee=fields["assignee"],
                due_date=fields["due_date"],
                labels=fields["labels"],
                source=source,
                dry_run=args.dry_run,
            )
            if success:
                written += 1
        else:
            write_backlog_md_directly(
                title=fields["title"],
                assignee=fields["assignee"],
                due_date=fields["due_date"],
                labels=fields["labels"],
                source=source,
                task_num=task_num,
                dry_run=args.dry_run,
            )
            written += 1
            task_num += 1

    print(f"\nDone: {written} imported, {flagged} skipped (low confidence)")
    if not args.dry_run and written:
        print("\nNext step: python scorer.py")


if __name__ == "__main__":
    main()
