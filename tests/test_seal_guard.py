import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "seal_guard.py"


def _run(file_path: str) -> str:
    payload = json.dumps({"tool_name": "Read", "tool_input": {"file_path": file_path}})
    proc = subprocess.run([sys.executable, str(HOOK)], input=payload,
                          capture_output=True, text=True)
    return proc.stdout


def test_denies_sealed_target():
    out = _run("/proj/.last-ds-mile/held/_sealed_target.csv")
    assert '"permissionDecision": "deny"' in out


def test_allows_held_features():
    out = _run("/proj/.last-ds-mile/held/features.csv")
    assert '"deny"' not in out


def test_allows_ordinary_file():
    out = _run("/proj/data/train.csv")
    assert '"deny"' not in out


def test_denies_sealed_target_windows_style_path():
    out = _run(r"C:\proj\.last-ds-mile\held\_sealed_target.csv")
    assert '"permissionDecision": "deny"' in out
