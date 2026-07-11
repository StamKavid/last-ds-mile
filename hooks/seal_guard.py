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
        parts = pure.parts
        name = pure.name
        if "held" in parts and name.startswith("_sealed"):
            return True
    return False


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # nothing to guard; stay out of the way

    file_path = str(data.get("tool_input", {}).get("file_path", ""))
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
