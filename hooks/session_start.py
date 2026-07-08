#!/usr/bin/env python3
"""SessionStart hook for last-ds-mile: prints a one-line safety posture summary
and current pipeline status. Reads only filenames under .last-ds-mile/ (never
file contents). See AUDIT.md for the full read/write contract."""
import json
import sys
from pathlib import Path


def stage_status(project_dir: Path) -> str:
    stages_dir = project_dir / ".last-ds-mile" / "stages"
    if not stages_dir.is_dir():
        return "no DS pipeline started yet"
    done = sorted(p.name for p in stages_dir.glob("*.md"))
    if not done:
        return "no DS pipeline started yet"
    return f"{len(done)} stage file(s) recorded, most recent: {done[-1]}"


def learnings_status(project_dir: Path) -> str:
    learnings_file = project_dir / ".last-ds-mile" / "learnings.jsonl"
    if not learnings_file.exists():
        return "no prior learnings recorded"
    try:
        text = learnings_file.read_text(encoding="utf-8")
    except OSError:
        return "learnings file present but unreadable"
    count = sum(1 for line in text.splitlines() if line.strip())
    return f"{count} prior session note(s) available"


def build_summary(cwd: str) -> str:
    project_dir = Path(cwd) if cwd else Path(".")
    return (
        "last-ds-mile safety posture: hooks are warn-don't-block (see AUDIT.md); "
        f"{stage_status(project_dir)}; {learnings_status(project_dir)}. "
        "Run /ds to see the pipeline map."
    )


def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    summary = build_summary(payload.get("cwd", ""))

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": summary,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
