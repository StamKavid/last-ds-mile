import json
import subprocess
import sys

from helpers import ROOT

HOOKS_DIR = ROOT / "hooks"


def run_hook(script_name: str, payload: dict) -> dict:
    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / script_name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"{script_name} exited {result.returncode}: {result.stderr}"
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_session_start_reports_no_pipeline_when_absent(tmp_path):
    out = run_hook("session_start.py", {"cwd": str(tmp_path)})
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "no DS pipeline started yet" in context
    assert "no prior learnings recorded" in context


def test_session_start_reports_stage_count(tmp_path):
    stages_dir = tmp_path / ".last-ds-mile" / "stages"
    stages_dir.mkdir(parents=True)
    (stages_dir / "00-frame.md").write_text("x", encoding="utf-8")
    (stages_dir / "01-data.md").write_text("x", encoding="utf-8")
    out = run_hook("session_start.py", {"cwd": str(tmp_path)})
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "2 stage file(s) recorded" in context
    assert "01-data.md" in context


def test_session_start_reports_learnings_count(tmp_path):
    ds_dir = tmp_path / ".last-ds-mile"
    ds_dir.mkdir(parents=True)
    (ds_dir / "learnings.jsonl").write_text('{"a": 1}\n{"b": 2}\n', encoding="utf-8")
    out = run_hook("session_start.py", {"cwd": str(tmp_path)})
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "2 prior session note(s) available" in context
