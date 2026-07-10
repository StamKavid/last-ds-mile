#!/usr/bin/env python3
"""SessionStart hook for last-ds-mile: prints a one-line safety posture summary,
current pipeline status, and any learnings relevant to the next stage. Reads only
filenames/frontmatter under .last-ds-mile/ and the plugin's own lessons/ directory
(never full lesson bodies, never other files). See AUDIT.md for the full read/write
contract."""
import json
import re
import sys
from pathlib import Path

STAGE_ORDER = [
    ("ds-frame", "00-frame.md"),
    ("ds-data", "01-data.md"),
    ("ds-explore", "02-explore.md"),
    ("ds-prep", "03-prep.md"),
    ("ds-baseline", "04-baseline.md"),
    ("ds-validate", "05-validate.md"),
    ("ds-model", "06-model.md"),
    ("ds-evaluate", "07-evaluate.md"),
    ("ds-explain", "08-explain.md"),
    ("ds-report", "09-report.md"),
    ("ds-handoff", "10-handoff.md"),
]

MAX_LESSONS_SURFACED = 3


def stage_status(project_dir: Path) -> str:
    stages_dir = project_dir / ".last-ds-mile" / "stages"
    if not stages_dir.is_dir():
        return "no DS pipeline started yet"
    done = sorted(p.name for p in stages_dir.glob("*.md"))
    if not done:
        return "no DS pipeline started yet"
    return f"{len(done)} stage file(s) recorded, most recent: {done[-1]}"


def next_stage(project_dir: Path) -> str:
    stages_dir = project_dir / ".last-ds-mile" / "stages"
    for name, filename in STAGE_ORDER:
        if not (stages_dir / filename).exists():
            return name
    return ""


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


def parse_bracket_list(text: str, key: str) -> list:
    match = re.search(rf"^{key}:\s*\[(.*?)\]\s*$", text, re.MULTILINE)
    if not match:
        return []
    return [item.strip() for item in match.group(1).split(",") if item.strip()]


def parse_frontmatter_title(text: str) -> str:
    match = re.search(r"^title:\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def matching_jsonl_lessons(project_dir: Path, stage: str) -> list:
    if not stage:
        return []
    learnings_file = project_dir / ".last-ds-mile" / "learnings.jsonl"
    if not learnings_file.exists():
        return []
    try:
        text = learnings_file.read_text(encoding="utf-8")
    except OSError:
        return []
    titles = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("type") == "lesson" and stage in record.get("tags", []):
            titles.append(record.get("title", "untitled lesson"))
    return titles


def matching_corpus_lessons(lessons_dir: Path, stage: str) -> list:
    if not stage or not lessons_dir.is_dir():
        return []
    titles = []
    for path in sorted(lessons_dir.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if stage in parse_bracket_list(text, "stages"):
            titles.append(parse_frontmatter_title(text) or path.stem)
    return titles


def relevant_lessons_line(project_dir: Path, lessons_dir: Path) -> str:
    stage = next_stage(project_dir)
    if not stage:
        return ""
    titles = matching_jsonl_lessons(project_dir, stage) + matching_corpus_lessons(lessons_dir, stage)
    if not titles:
        return ""
    shown = titles[:MAX_LESSONS_SURFACED]
    return f" Relevant lessons for {stage}: " + "; ".join(shown) + "."


def build_summary(cwd: str, lessons_dir: Path) -> str:
    project_dir = Path(cwd) if cwd else Path(".")
    return (
        "last-ds-mile safety posture: hooks are warn-don't-block (see AUDIT.md); "
        f"{stage_status(project_dir)}; {learnings_status(project_dir)}."
        f"{relevant_lessons_line(project_dir, lessons_dir)}"
        " Run /ds to see the pipeline map."
    )


def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    lessons_dir = Path(__file__).resolve().parent.parent / "lessons"
    summary = build_summary(payload.get("cwd", ""), lessons_dir)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": summary,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
