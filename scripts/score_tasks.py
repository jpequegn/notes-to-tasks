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
            fm = _minimal_yaml_parse(fm_text)
    else:
        fm = _minimal_yaml_parse(fm_text)

    return fm, body


def _minimal_yaml_parse(fm_text: str) -> dict:
    """Minimal YAML parser for key: value pairs; handles JSON-array strings."""
    import json as _json
    fm: dict = {}
    for line in fm_text.splitlines():
        m = re.match(r'^(\w[\w_-]*):\s*(.*)$', line)
        if not m:
            continue
        key = m.group(1)
        raw = m.group(2).strip()
        # JSON array value (may or may not be quoted)
        inner = raw.strip('"\'')
        if inner.startswith("[") and inner.endswith("]"):
            try:
                fm[key] = _json.loads(inner)
                continue
            except ValueError:
                pass
        if raw.lower() in ("null", "~", ""):
            fm[key] = None
        elif re.match(r'^-?\d+\.\d+$', raw):
            fm[key] = float(raw)
        elif re.match(r'^-?\d+$', raw):
            fm[key] = int(raw)
        else:
            fm[key] = raw.strip('"\'')
    return fm


def render_frontmatter(fm: dict) -> str:
    """Render frontmatter dict back to YAML string."""
    import json as _json
    lines = []
    for key, val in fm.items():
        if val is None:
            lines.append(f"{key}: null")
        elif isinstance(val, list):
            lines.append(f"{key}: {_json.dumps(val)}")
        elif isinstance(val, str):
            # Guard: if a string looks like a JSON array (corrupted round-trip),
            # parse it back to a list and emit properly.
            stripped = val.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    parsed = _json.loads(stripped)
                    if isinstance(parsed, list):
                        lines.append(f"{key}: {_json.dumps(parsed)}")
                        continue
                except ValueError:
                    pass
            lines.append(f'{key}: "{val}"')
        elif isinstance(val, float):
            lines.append(f"{key}: {val:.1f}")
        else:
            lines.append(f"{key}: {val}")
    return "\n".join(lines)


def compute_urgency(fm: dict, body: str = "") -> int:
    """Rule-based urgency: keyword detection + deadline proximity.

    Uses extracted urgency from frontmatter as the keyword baseline (set during
    extraction against the full raw action item text), then always applies
    deadline proximity on top — the early-return pattern previously skipped this.
    """
    stored = fm.get("urgency")
    if isinstance(stored, int) and stored > 0:
        # Use the extraction-time keyword score as the starting point.
        # It was computed against the full raw action item (including trailing
        # "blocking X" / "depends on Y" annotations that don't survive into title).
        score = stored
    else:
        score = 5  # base
        searchable = " ".join([
            str(fm.get("title", "")),
            body,
        ]).lower()
        for kw, boost in URGENCY_KEYWORDS.items():
            if kw in searchable:
                score = min(10, score + boost)

    # Always apply deadline proximity — this was the bug.
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

    return min(10, score)


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


def llm_score_impact_effort(fm: dict, body: str = "") -> tuple[int, int] | None:
    """
    Score impact and effort via Anthropic claude-haiku-4-5.
    Returns (impact, effort) or None if unavailable.
    """
    import json as _json

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
    except ImportError:
        print("  [anthropic not installed — pip install anthropic]")
        return None

    impact_rubric = (PROMPTS_DIR / "impact_rubric.md").read_text()
    effort_rubric = (PROMPTS_DIR / "effort_rubric.md").read_text()

    title = fm.get("title", "")
    labels = fm.get("labels") or []
    due_date = fm.get("due_date") or "none"
    source = fm.get("source") or "unknown"
    context = body[:600].strip() if body else "none"

    prompt = f"""Score the following task for impact and effort. Be precise — use the full 1–10 range.

Task title: {title}
Labels: {", ".join(labels) if labels else "none"}
Due date: {due_date}
Source: {source}
Body context: {context}

---
{impact_rubric}

---
{effort_rubric}

---
Return ONLY a JSON object, no other text:
{{"impact": <integer 1-10>, "effort": <integer 1-10>, "impact_rationale": "<one sentence>", "effort_rationale": "<one sentence>"}}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        block = message.content[0]
        if not hasattr(block, "text"):
            return None
        text = block.text.strip()  # type: ignore[union-attr]
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        data = _json.loads(m.group())
        impact = max(1, min(10, int(data["impact"])))
        effort = max(1, min(10, int(data["effort"])))
        impact_r = data.get("impact_rationale", "")
        effort_r = data.get("effort_rationale", "")
        print(f"  [LLM] impact={impact} ({impact_r[:60]})")
        print(f"  [LLM] effort={effort} ({effort_r[:60]})")
        return impact, effort
    except Exception as e:
        print(f"  [LLM error: {e}]")
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

    urgency = compute_urgency(fm, body)

    impact = fm.get("impact")
    effort = fm.get("effort")

    if (impact is None or effort is None) and not no_llm:
        llm_result = llm_score_impact_effort(fm, body)
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
