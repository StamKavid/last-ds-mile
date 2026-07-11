#!/usr/bin/env python3
"""PreToolUse hook for last-ds-mile: denies the agent read-access to the SEALED
holdout labels (any file named `_sealed_*` under `.last-ds-mile/held/`). This is
the one deliberately blocking hook in the plugin (the safe-set default is
warn-don't-block) because it is the physical basis of the Sealed Bet's trust
guarantee. The held *features* file stays readable — only the labels are sealed.
Reads only the tool_input path from stdin; touches no files. See AUDIT.md."""
import json
import sys
from pathlib import PurePosixPath, PureWindowsPath


def _is_sealed(file_path: str) -> bool:
    for pure in (PurePosixPath(file_path), PureWindowsPath(file_path)):
        # Windows silently strips trailing dots/spaces from a path component
        # before resolving it on disk (Win32 CreateFile normalization), so
        # "held." and "held " on disk are the same directory as "held". Strip
        # them here too, or a crafted "held." component would sail past this
        # check while the real filesystem still serves the sealed file.
        parts = tuple(p.lower().rstrip(". ") for p in pure.parts)
        name = pure.name.lower()
        if "held" in parts and name.startswith("_sealed"):
            return True
    return False


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # nothing to guard; stay out of the way

    if not isinstance(data, dict):
        sys.exit(0)  # not a normal tool-use payload; nothing to check

    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    file_path = str(tool_input.get("file_path", ""))
    if file_path and _is_sealed(file_path):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "The sealed holdout labels are off-limits — that is the whole "
                    "point of the Sealed Bet. Build on dev; open once via "
                    "`python -m sealed_bet.score --preds <your_preds.csv>`."
                ),
            }
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()
