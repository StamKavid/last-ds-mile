#!/usr/bin/env python3
"""Stop hook for last-ds-mile: appends a raw session note to the local
learnings store. This is raw material for a future curation workflow
(the plugin's Plan 4), not a curated lesson itself. See AUDIT.md."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    cwd = payload.get("cwd") or "."
    project_dir = Path(cwd)
    ds_dir = project_dir / ".last-ds-mile"
    stages_dir = ds_dir / "stages"

    if not stages_dir.is_dir():
        sys.exit(0)  # DS pipeline never started this session, nothing to record

    stage_files = sorted(p.name for p in stages_dir.glob("*.md"))
    if not stage_files:
        sys.exit(0)

    note = {
        "type": "session",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "session_id": payload.get("session_id", "unknown"),
        "stage_files": stage_files,
    }

    try:
        ds_dir.mkdir(parents=True, exist_ok=True)
        learnings_file = ds_dir / "learnings.jsonl"
        with learnings_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(note) + "\n")
    except OSError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
