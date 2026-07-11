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


def test_denies_case_variant_path():
    out = _run("/proj/.last-ds-mile/HELD/_SEALED_target.csv")
    assert '"permissionDecision": "deny"' in out


def test_handles_null_tool_input_without_crashing():
    payload = json.dumps({"tool_name": "Read", "tool_input": None})
    proc = subprocess.run([sys.executable, str(HOOK)], input=payload,
                          capture_output=True, text=True)
    assert proc.returncode == 0
    assert '"deny"' not in proc.stdout


def test_handles_non_dict_payload_without_crashing():
    for payload in ('[1, 2, 3]', '"just a string"', 'null', '42'):
        proc = subprocess.run([sys.executable, str(HOOK)], input=payload,
                              capture_output=True, text=True)
        assert proc.returncode == 0, f"crashed on payload {payload!r}: {proc.stderr}"
        assert '"deny"' not in proc.stdout


def test_denies_trailing_dot_directory_bypass(tmp_path):
    # Build a real sealed file on disk and confirm the OS actually resolves
    # the trailing-dot path to it (proving the bypass would matter), THEN
    # confirm the hook denies the crafted path string.
    held_dir = tmp_path / "held"
    held_dir.mkdir()
    real_file = held_dir / "_sealed_target.csv"
    real_file.write_text("y\n1\n0\n", encoding="utf-8")

    crafted_path = str(tmp_path / "held." / "_sealed_target.csv")
    out = _run(crafted_path)
    assert '"permissionDecision": "deny"' in out


def test_denies_trailing_space_directory_bypass():
    out = _run("/proj/.last-ds-mile/held /_sealed_target.csv")
    assert '"permissionDecision": "deny"' in out


def test_handles_truthy_non_dict_tool_input_without_crashing():
    for tool_input_json in ('"held/_sealed_target.csv"', '["a", "b"]', '42',
                             'true', '3.14'):
        payload = f'{{"tool_name": "Read", "tool_input": {tool_input_json}}}'
        proc = subprocess.run([sys.executable, str(HOOK)], input=payload,
                              capture_output=True, text=True)
        assert proc.returncode == 0, f"crashed on tool_input={tool_input_json}: {proc.stderr}"
        assert '"deny"' not in proc.stdout
