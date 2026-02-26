#!/usr/bin/env python3
"""
scorer.py — AI scoring layer for Backlog.md tasks

Reads tasks from backlog/tasks/, computes score using the shared formula,
and writes score/urgency/impact/effort back to frontmatter.

Usage:
    python scorer.py              # score all tasks
    python scorer.py --dry-run    # preview without writing
    python scorer.py --list       # list tasks sorted by score
    python scorer.py --no-llm     # rule-based only
"""

import argparse
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).parent
REPO_ROOT = IMPL_DIR.parent.parent
BACKLOG_DIR = IMPL_DIR / "backlog" / "tasks"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
try:
    from score_tasks import (
        compute_urgency, heuristic_impact_effort, compute_score,
        parse_frontmatter, render_frontmatter, llm_score_impact_effort
    )
    HAS_SCORER = True
except ImportError:
    HAS_SCORER = False


def parse_args():
    parser = argparse.ArgumentParser(description="Score Backlog.md tasks")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--list", action="store_true", help="List scored tasks by priority")
    parser.add_argument("--no-llm", action="store_true", help="Rule-based scoring only")
    return parser.parse_args()


def main():
    args = parse_args()

    if not HAS_SCORER:
        print("Error: could not import scoring functions from scripts/score_tasks.py")
        sys.exit(1)

    if not BACKLOG_DIR.exists():
        print(f"No tasks directory found at {BACKLOG_DIR}")
        print("Run: python importer.py ../../meeting-notes/<file>.md")
        sys.exit(0)

    task_files = sorted(BACKLOG_DIR.glob("*.md"))
    if not task_files:
        print("No task files found.")
        sys.exit(0)

    print(f"Found {len(task_files)} task(s) in {BACKLOG_DIR}\n")

    results = []
    from datetime import date
    today = date.today().isoformat()

    for path in task_files:
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        if not fm:
            print(f"  SKIP {path.name}: no frontmatter")
            continue

        urgency = compute_urgency(fm)
        impact = fm.get("impact")
        effort = fm.get("effort")

        if (impact is None or effort is None) and not args.no_llm:
            llm_result = llm_score_impact_effort(fm)
            if llm_result:
                impact, effort = llm_result

        if impact is None or effort is None:
            impact_h, effort_h = heuristic_impact_effort(fm)
            impact = impact if impact is not None else impact_h
            effort = effort if effort is not None else effort_h

        score = compute_score(urgency, impact, effort)

        title = fm.get("title", path.stem)
        action = "Would set" if args.dry_run else "Scored"
        print(f"  {action} {path.name}: score={score} "
              f"(u={urgency} i={impact} e={effort}) — {str(title)[:40]}")

        results.append({"path": path, "fm": fm, "body": body,
                        "score": score, "urgency": urgency,
                        "impact": impact, "effort": effort, "title": title})

        if not args.dry_run:
            fm["score"] = score
            fm["urgency"] = urgency
            fm["impact"] = impact
            fm["effort"] = effort
            fm["updated"] = today
            content = f"---\n{render_frontmatter(fm)}\n---\n\n{body}"
            path.write_text(content, encoding="utf-8")

    if args.list and results:
        results.sort(key=lambda r: r["score"], reverse=True)
        print(f"\n{'─'*60}")
        print("  Priority ranking:")
        for r in results:
            print(f"  {r['score']:4.1f}  {r['path'].name}  {str(r['title'])[:45]}")

    print(f"\n{'─'*60}")
    print(f"  {len(results)} task(s) scored")
    if args.dry_run:
        print("  (dry run — no files written)")


if __name__ == "__main__":
    main()
