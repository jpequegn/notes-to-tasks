#!/usr/bin/env python3
"""
daily-brief.py — Generate today's priority view for Implementation B

Usage:
    python daily-brief.py
    python daily-brief.py --limit 10
    python daily-brief.py --status todo
    python daily-brief.py --assignee @alice
"""

import argparse
import re
from datetime import date
from pathlib import Path

IMPL_DIR = Path(__file__).parent
TASKS_DIR = IMPL_DIR / "tasks"


def parse_args():
    parser = argparse.ArgumentParser(description="Today's task priorities")
    parser.add_argument("--limit", type=int, default=20, help="Max tasks to show")
    parser.add_argument("--status", default="todo,in-progress",
                        help="Comma-separated statuses to include (default: todo,in-progress)")
    parser.add_argument("--assignee", help="Filter by assignee (@username)")
    parser.add_argument("--all", action="store_true", help="Show all statuses")
    return parser.parse_args()


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm_text = text[3:end].strip()
    fm: dict = {}
    for line in fm_text.splitlines():
        m = re.match(r'^(\w[\w_-]*):\s*(.*)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip().strip('"\'')
            if val.lower() in ("null", "~", ""):
                fm[key] = None
            elif re.match(r'^\d+\.\d+$', val):
                fm[key] = float(val)
            elif re.match(r'^\d+$', val):
                fm[key] = int(val)
            else:
                fm[key] = val
    return fm


def load_tasks(statuses: set[str], assignee: str | None) -> list[dict]:
    if not TASKS_DIR.exists():
        return []

    tasks = []
    for path in TASKS_DIR.glob("TASK-*.md"):
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if not fm:
            continue
        if fm.get("status") not in statuses:
            continue
        if assignee and fm.get("assignee") != assignee:
            continue
        fm["_path"] = str(path)
        tasks.append(fm)

    return sorted(tasks, key=lambda t: (t.get("score") or 0), reverse=True)


def priority_bar(score: float | None) -> str:
    if score is None:
        return "░░░░░░░░░░ (unscored)"
    filled = round(score)
    empty = 10 - filled
    bar = "█" * filled + "░" * empty
    if score >= 8:
        label = "CRITICAL"
    elif score >= 6:
        label = "HIGH    "
    elif score >= 4:
        label = "MEDIUM  "
    else:
        label = "LOW     "
    return f"{bar} {score:.1f} {label}"


def due_indicator(due_date: str | None) -> str:
    if not due_date or due_date == "null":
        return ""
    try:
        due = date.fromisoformat(str(due_date))
        days = (due - date.today()).days
        if days < 0:
            return f" ⚠️  OVERDUE ({abs(days)}d ago)"
        elif days == 0:
            return " 🔴 DUE TODAY"
        elif days <= 2:
            return f" 🟠 DUE IN {days}d"
        elif days <= 7:
            return f" 🟡 DUE IN {days}d"
        else:
            return f" (due {due_date})"
    except ValueError:
        return f" (due {due_date})"


def main():
    args = parse_args()
    today = date.today().isoformat()

    if args.all:
        statuses = {"todo", "in-progress", "review", "done", "blocked"}
    else:
        statuses = set(args.status.split(","))

    tasks = load_tasks(statuses, args.assignee)

    print(f"\n{'='*60}")
    print(f"  DAILY BRIEF — {today}")
    print(f"  Implementation B (Pure Markdown)")
    print(f"{'='*60}")

    if not tasks:
        print("\n  No tasks found.")
        print(f"  Task directory: {TASKS_DIR}")
        print("\n  To create tasks:")
        print("    python ../../scripts/extract_tasks.py ../../meeting-notes/<file>.md --impl B")
        print(f"{'='*60}\n")
        return

    shown = tasks[:args.limit]
    print(f"\n  Showing {len(shown)} of {len(tasks)} task(s) | statuses: {', '.join(sorted(statuses))}\n")

    for task in shown:
        task_id = task.get("id", "?")
        title = task.get("title", "Untitled")
        status = task.get("status", "?")
        assignee = task.get("assignee", "unassigned")
        score = task.get("score")
        due = task.get("due_date")

        status_icon = {
            "todo": "○",
            "in-progress": "◐",
            "review": "◑",
            "done": "●",
            "blocked": "✗",
        }.get(status, "?")

        print(f"  {status_icon} {task_id}  [{assignee}]")
        print(f"    {title[:56]}{due_indicator(due)}")
        print(f"    {priority_bar(score)}")
        print()

    if len(tasks) > args.limit:
        print(f"  ... and {len(tasks) - args.limit} more. Use --limit to see more.\n")

    # Summary
    todo_count = sum(1 for t in tasks if t.get("status") == "todo")
    in_prog = sum(1 for t in tasks if t.get("status") == "in-progress")
    blocked = sum(1 for t in tasks if t.get("status") == "blocked")

    print(f"{'='*60}")
    print(f"  Summary: {todo_count} todo | {in_prog} in-progress | {blocked} blocked")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
