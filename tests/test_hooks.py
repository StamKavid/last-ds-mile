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


def test_session_start_does_not_crash_when_learnings_file_is_unreadable(tmp_path):
    ds_dir = tmp_path / ".last-ds-mile"
    ds_dir.mkdir(parents=True)
    # learnings.jsonl exists as a DIRECTORY, not a file — .exists() is True but
    # read_text() raises IsADirectoryError (an OSError subclass).
    (ds_dir / "learnings.jsonl").mkdir()

    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "session_start.py")],
        input=json.dumps({"cwd": str(tmp_path)}),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"session_start.py should not crash: {result.stderr}"


def test_scan_flags_out_of_workspace_pickle(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    pkl_path = outside / "model.pkl"
    pkl_path.write_bytes(b"not a real pickle, just bytes")

    out = run_hook("scan_untrusted_input.py", {
        "tool_name": "Read",
        "tool_input": {"file_path": str(pkl_path)},
        "cwd": str(workspace),
    })
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "pickle/joblib file outside the project workspace" in context


def test_scan_does_not_flag_in_workspace_pickle(tmp_path):
    pkl_path = tmp_path / "model.pkl"
    pkl_path.write_bytes(b"not a real pickle, just bytes")

    out = run_hook("scan_untrusted_input.py", {
        "tool_name": "Read",
        "tool_input": {"file_path": str(pkl_path)},
        "cwd": str(tmp_path),
    })
    assert out == {}


def test_scan_flags_secret_looking_csv_header(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("user_id,api_key,value\n1,abc,10\n", encoding="utf-8")

    out = run_hook("scan_untrusted_input.py", {
        "tool_name": "Read",
        "tool_input": {"file_path": str(csv_path)},
        "cwd": str(tmp_path),
    })
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "looks like it names a secret" in context


def test_scan_flags_hidden_unicode_in_csv(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b\n1​,2\n", encoding="utf-8")

    out = run_hook("scan_untrusted_input.py", {
        "tool_name": "Read",
        "tool_input": {"file_path": str(csv_path)},
        "cwd": str(tmp_path),
    })
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "hidden/bidi-override unicode" in context


def test_scan_ignores_non_ipynb_edits(tmp_path):
    out = run_hook("scan_untrusted_input.py", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(tmp_path / "script.py"), "content": "pickle.load(open('x'))"},
        "cwd": str(tmp_path),
    })
    assert out == {}


def test_scan_flags_pickle_load_in_notebook_edit(tmp_path):
    out = run_hook("scan_untrusted_input.py", {
        "tool_name": "Write",
        "tool_input": {
            "file_path": str(tmp_path / "notebook.ipynb"),
            "content": "import pickle\nmodel = pickle.load(open('model.pkl', 'rb'))",
        },
        "cwd": str(tmp_path),
    })
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "calls pickle.load()/joblib.load()" in context


def test_scan_flags_shell_magic_in_notebook_edit(tmp_path):
    out = run_hook("scan_untrusted_input.py", {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(tmp_path / "notebook.ipynb"),
            "new_string": "!pip install some-package",
        },
        "cwd": str(tmp_path),
    })
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "Shell magic in notebook cell" in context


def test_scan_flags_pickle_when_cwd_missing(tmp_path):
    pkl_path = tmp_path / "model.pkl"
    pkl_path.write_bytes(b"not a real pickle, just bytes")

    out = run_hook("scan_untrusted_input.py", {
        "tool_name": "Read",
        "tool_input": {"file_path": str(pkl_path)},
        "cwd": "",
    })
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "could not determine the project workspace" in context


def test_scan_flags_shell_magic_with_space_after_bang(tmp_path):
    out = run_hook("scan_untrusted_input.py", {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(tmp_path / "notebook.ipynb"),
            "new_string": "! pip install some-package",
        },
        "cwd": str(tmp_path),
    })
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "Shell magic in notebook cell" in context


def test_pre_compact_writes_snapshot_with_stage_files(tmp_path):
    stages_dir = tmp_path / ".last-ds-mile" / "stages"
    stages_dir.mkdir(parents=True)
    (stages_dir / "00-frame.md").write_text("x", encoding="utf-8")

    run_hook("pre_compact.py", {"cwd": str(tmp_path), "trigger": "manual"})

    state_file = tmp_path / ".last-ds-mile" / "session-state.json"
    assert state_file.exists()
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["trigger"] == "manual"
    assert data["stage_files"] == ["00-frame.md"]


def test_pre_compact_writes_empty_stage_list_when_no_pipeline(tmp_path):
    run_hook("pre_compact.py", {"cwd": str(tmp_path), "trigger": "auto"})

    state_file = tmp_path / ".last-ds-mile" / "session-state.json"
    assert state_file.exists()
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["stage_files"] == []


def test_pre_compact_does_not_crash_when_ds_dir_path_is_a_file(tmp_path):
    # .last-ds-mile already exists as a FILE, not a directory — mkdir() would raise.
    (tmp_path / ".last-ds-mile").write_text("not a directory", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "pre_compact.py")],
        input=json.dumps({"cwd": str(tmp_path), "trigger": "manual"}),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"pre_compact.py should not crash: {result.stderr}"


def test_stop_appends_learning_when_pipeline_started(tmp_path):
    stages_dir = tmp_path / ".last-ds-mile" / "stages"
    stages_dir.mkdir(parents=True)
    (stages_dir / "00-frame.md").write_text("x", encoding="utf-8")

    run_hook("stop_persist_learnings.py", {"cwd": str(tmp_path), "session_id": "abc123"})

    learnings_file = tmp_path / ".last-ds-mile" / "learnings.jsonl"
    assert learnings_file.exists()
    lines = learnings_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    note = json.loads(lines[0])
    assert note["session_id"] == "abc123"
    assert note["stage_files"] == ["00-frame.md"]


def test_stop_does_not_write_when_no_pipeline(tmp_path):
    run_hook("stop_persist_learnings.py", {"cwd": str(tmp_path), "session_id": "abc123"})

    learnings_file = tmp_path / ".last-ds-mile" / "learnings.jsonl"
    assert not learnings_file.exists()


def test_stop_appends_second_line_on_second_call(tmp_path):
    stages_dir = tmp_path / ".last-ds-mile" / "stages"
    stages_dir.mkdir(parents=True)
    (stages_dir / "00-frame.md").write_text("x", encoding="utf-8")

    run_hook("stop_persist_learnings.py", {"cwd": str(tmp_path), "session_id": "first"})
    run_hook("stop_persist_learnings.py", {"cwd": str(tmp_path), "session_id": "second"})

    learnings_file = tmp_path / ".last-ds-mile" / "learnings.jsonl"
    lines = learnings_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_stop_note_has_type_session(tmp_path):
    stages_dir = tmp_path / ".last-ds-mile" / "stages"
    stages_dir.mkdir(parents=True)
    (stages_dir / "00-frame.md").write_text("x", encoding="utf-8")

    run_hook("stop_persist_learnings.py", {"cwd": str(tmp_path), "session_id": "abc123"})

    learnings_file = tmp_path / ".last-ds-mile" / "learnings.jsonl"
    note = json.loads(learnings_file.read_text(encoding="utf-8").splitlines()[0])
    assert note["type"] == "session"
