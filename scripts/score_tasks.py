#!/usr/bin/env python3
"""
score_tasks.py — Multi-factor scoring engine

Computes score = (urgency × 0.4) + (impact × 0.4) - (effort × 0.2)

- urgency: rule-based (deadline proximity + keywords) — runs without LLM
- impact/effort: LLM-scored via rubric prompts — requires ANTHROPIC_API_KEY or GEMINI_API_KEY
  If no LLM key available, falls back to heuristic scoring.

Usage:
    python3 scripts/score_tasks.py                    # score all implementations
    python3 scripts/score_tasks.py --impl B           # score only Implementation B
    python3 scripts/score_tasks.py --dry-run          # preview scores without writing
    python3 scripts/score_tasks.py --no-llm           # rule-based only, no LLM calls
"""

import argparse
import os
import re
from datetime import date, datetime
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:  # pragma: no cover
    HAS_YAML = False

REPO_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = REPO_ROOT / "scripts" / "prompts"

IMPL_TASK_DIRS = {
    "A": REPO_ROOT / "implementations" / "A-mcp-server" / "tasks",
    "B": REPO_ROOT / "implementations" / "B-pure-markdown" / "tasks",
    "C": REPO_ROOT / "implementations" / "C-backlog-md" / "backlog",
}

URGENCY_KEYWORDS = {
    "blocking": 3, "blocked": 3, "critical": 3, "p0": 3,
    "asap": 2, "urgent": 2, "immediately": 2, "today": 2, "eod": 2, "p1": 2,
    "high priority": 1, "soon": 1,
}

SCORE_WEIGHTS = {"urgency": 0.4, "impact": 0.4, "effort": -0.2}


def parse_args():
    parser = argparse.ArgumentParser(description="Score tasks using multi-factor engine")
    parser.add_argument("--impl", choices=["A", "B", "C"], help="Score only one implementation")
    parser.add_argument("--dry-run", action="store_true", help="Preview scores without writing")
    parser.add_argument("--no-llm", action="store_true", help="Rule-based scoring only, no LLM")
    return parser.parse_args()


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from markdown."""
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_text = text[3:end].strip()
    body = text[end + 4:].strip()

    if HAS_YAML:
        try:
            fm = yaml.safe_load(fm_text) or {}  # type: ignore[possibly-undefined]
        except yaml.YAMLError:  # type: ignore[possibly-undefined]
            fm = {}
    else:
        # Minimal YAML parser for key: value pairs
        fm = {}
        for line in fm_text.splitlines():
            m = re.match(r'^(\w[\w_-]*):\s*(.+)$', line)
            if m:
                key, val = m.group(1), m.group(2).strip().strip('"\'')
                if val.lower() == "null":
                    fm[key] = None
                elif re.match(r'^\d+\.\d+$', val):
                    fm[key] = float(val)
                elif re.match(r'^\d+$', val):
                    fm[key] = int(val)
                else:
                    fm[key] = val

    return fm, body


def render_frontmatter(fm: dict) -> str:
    """Render frontmatter dict back to YAML string."""
    lines = []
    for key, val in fm.items():
        if val is None:
            lines.append(f"{key}: null")
        elif isinstance(val, str):
            lines.append(f'{key}: "{val}"')
        elif isinstance(val, list):
            import json
            lines.append(f"{key}: {json.dumps(val)}")
        elif isinstance(val, float):
            lines.append(f"{key}: {val:.1f}")
        else:
            lines.append(f"{key}: {val}")
    return "\n".join(lines)


def compute_urgency(fm: dict) -> int:
    """Rule-based urgency: deadline proximity + keyword detection."""
    urgency = fm.get("urgency")
    if isinstance(urgency, int) and urgency > 0:
        return urgency  # already set (e.g. by extract_tasks.py)

    score = 5  # base

    # Keyword detection across title + any text fields
    searchable = " ".join([
        str(fm.get("title", "")),
        str(fm.get("notes", "")),
    ]).lower()

    for kw, boost in URGENCY_KEYWORDS.items():
        if kw in searchable:
            score = min(10, score + boost)

    # Deadline proximity
    due = fm.get("due_date")
    if due and due not in ("null", None, ""):
        try:
            due_date = datetime.strptime(str(due), "%Y-%m-%d").date()
            days_left = (due_date - date.today()).days
            if days_left <= 0:
                score = min(10, score + 4)
            elif days_left <= 2:
                score = min(10, score + 3)
            elif days_left <= 7:
                score = min(10, score + 2)
            elif days_left <= 14:
                score = min(10, score + 1)
        except ValueError:
            pass

    return score


def heuristic_impact_effort(fm: dict) -> tuple[int, int]:
    """
    Heuristic fallback when LLM is unavailable.
    Returns (impact, effort) as integers 1-10.
    """
    title_lower = str(fm.get("title", "")).lower()
    priority = str(fm.get("priority", "medium")).lower()

    # Impact heuristics
    impact = 6  # base
    if priority == "critical":
        impact = 9
    elif priority == "high":
        impact = 7
    elif priority == "low":
        impact = 3

    high_impact_keywords = ["launch", "release", "customer", "revenue", "security", "auth",
                            "production", "deploy", "outage", "critical", "blocking"]
    for kw in high_impact_keywords:
        if kw in title_lower:
            impact = min(10, impact + 1)

    # Effort heuristics
    effort = 4  # base (medium)
    hard_keywords = ["refactor", "migrate", "redesign", "architecture", "integration",
                     "rewrite", "research", "spike"]
    easy_keywords = ["fix typo", "update readme", "update doc", "bump version", "hotfix"]

    for kw in hard_keywords:
        if kw in title_lower:
            effort = min(10, effort + 2)
    for kw in easy_keywords:
        if kw in title_lower:
            effort = max(1, effort - 2)

    return impact, effort


def llm_score_impact_effort(fm: dict) -> tuple[int, int] | None:
    """
    LLM-based scoring using rubric prompts.
    Returns (impact, effort) or None if LLM unavailable.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    impact_prompt_path = PROMPTS_DIR / "impact_rubric.md"
    effort_prompt_path = PROMPTS_DIR / "effort_rubric.md"

    if not impact_prompt_path.exists() or not effort_prompt_path.exists():
        return None

    # LLM integration stub — implement with your preferred client
    # Example with Anthropic:
    # from anthropic import Anthropic
    # client = Anthropic()
    # ...
    print("  [LLM scoring not yet implemented — using heuristics]")
    return None


def compute_score(urgency: int, impact: int, effort: int) -> float:
    return round(
        urgency * SCORE_WEIGHTS["urgency"]
        + impact * SCORE_WEIGHTS["impact"]
        + effort * SCORE_WEIGHTS["effort"],
        1
    )


def score_task_file(path: Path, dry_run: bool, no_llm: bool) -> dict:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    if not fm:
        return {"path": path, "status": "skipped", "reason": "no frontmatter"}

    urgency = compute_urgency(fm)

    impact = fm.get("impact")
    effort = fm.get("effort")

    if (impact is None or effort is None) and not no_llm:
        llm_result = llm_score_impact_effort(fm)
        if llm_result:
            impact, effort = llm_result

    if impact is None or effort is None:
        impact_h, effort_h = heuristic_impact_effort(fm)
        impact = impact if impact is not None else impact_h
        effort = effort if effort is not None else effort_h

    score = compute_score(urgency, impact, effort)
    today = date.today().isoformat()

    result = {
        "path": path,
        "id": fm.get("id", path.stem),
        "title": fm.get("title", ""),
        "urgency": urgency,
        "impact": impact,
        "effort": effort,
        "score": score,
        "status": "scored",
    }

    if not dry_run:
        fm["urgency"] = urgency
        fm["impact"] = impact
        fm["effort"] = effort
        fm["score"] = score
        fm["updated_date"] = today

        new_text = f"---\n{render_frontmatter(fm)}\n---\n\n{body}"
        path.write_text(new_text, encoding="utf-8")

    return result


def main():
    args = parse_args()

    if not HAS_YAML:
        print("Note: pyyaml not installed — using minimal YAML parser (pip install pyyaml for full support)")

    impls = [args.impl] if args.impl else ["A", "B", "C"]
    all_results = []

    for impl in impls:
        task_dir = IMPL_TASK_DIRS[impl]
        if not task_dir.exists():
            continue

        task_files = sorted(task_dir.glob("TASK-*.md"))
        if not task_files:
            continue

        print(f"\nImplementation {impl} — {len(task_files)} task(s) in {task_dir}")

        for task_file in task_files:
            result = score_task_file(task_file, args.dry_run, args.no_llm)
            all_results.append(result)

            if result["status"] == "skipped":
                print(f"  SKIP {task_file.name}: {result['reason']}")
            else:
                action = "Would set" if args.dry_run else "Scored"
                print(f"  {action} {result['id']}: score={result['score']} "
                      f"(u={result['urgency']} i={result['impact']} e={result['effort']}) "
                      f"— {str(result['title'])[:40]}")

    scored = [r for r in all_results if r["status"] == "scored"]
    if scored:
        print(f"\nTotal: {len(scored)} task(s) scored")
        if args.dry_run:
            print("(dry run — no files written)")

        # Show top 5
        top = sorted(scored, key=lambda r: r["score"], reverse=True)[:5]
        if len(scored) > 1:
            print("\nTop priority tasks:")
            for r in top:
                print(f"  {r['score']:4.1f}  {r['id']}  {str(r['title'])[:50]}")
    else:
        print("\nNo tasks found. Run extract_tasks.py first.")


if __name__ == "__main__":
    main()
