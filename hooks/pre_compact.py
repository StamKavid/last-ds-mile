#!/usr/bin/env python3
"""PreCompact hook for last-ds-mile: snapshots DS session state before context
compaction so /ds can resume cleanly afterward. See AUDIT.md."""
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

    stage_files = sorted(p.name for p in stages_dir.glob("*.md")) if stages_dir.is_dir() else []

    snapshot = {
        "snapshotted_at": datetime.now(timezone.utc).isoformat(),
        "trigger": payload.get("trigger", "unknown"),
        "stage_files": stage_files,
    }

    ds_dir.mkdir(parents=True, exist_ok=True)
    state_file = ds_dir / "session-state.json"
    state_file.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")

    sys.exit(0)


if __name__ == "__main__":
    main()
