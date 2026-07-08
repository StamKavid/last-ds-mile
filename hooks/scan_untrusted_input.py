#!/usr/bin/env python3
"""PostToolUse hook for last-ds-mile: flags untrusted-input risks in data files
and notebooks. Warn-don't-block: always exits 0, never blocks the tool call.
Reads only the specific file the agent just touched, never a directory sweep.
See AUDIT.md for the full read/write contract."""
import json
import re
import sys
from pathlib import Path

PICKLE_RE = re.compile(r"\b(pickle|joblib)\.load\s*\(")
SHELL_MAGIC_RE = re.compile(r"^\s*!\S")
SECRET_NAME_RE = re.compile(
    r"\b(api[_-]?key|secret|password|passwd|token|access[_-]?key)\b", re.IGNORECASE
)
SECRET_VALUE_RE = re.compile(r"\b[A-Za-z0-9+/]{32,}={0,2}\b")
HIDDEN_UNICODE_CHARS = {
    "​", "‌", "‍", "‎", "‏",  # zero-width / directional marks
    "‪", "‫", "‬", "‭", "‮",  # bidi embedding/override
    "⁦", "⁧", "⁨", "⁩",  # bidi isolates
}
PICKLE_EXTENSIONS = {".pkl", ".joblib"}
DATA_READ_EXTENSIONS = {".csv", ".parquet", ".xlsx", ".pkl", ".joblib"}


def find_hidden_unicode(text: str) -> set:
    return {ch for ch in text if ch in HIDDEN_UNICODE_CHARS}


def scan_read(file_path: str, cwd: str) -> list:
    findings = []
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix not in DATA_READ_EXTENSIONS:
        return findings

    if suffix in PICKLE_EXTENSIONS:
        try:
            resolved = path.resolve()
            project_dir = Path(cwd).resolve() if cwd else None
        except OSError:
            return findings
        if project_dir and project_dir != resolved and project_dir not in resolved.parents:
            findings.append(
                f"{path.name} is a pickle/joblib file outside the project workspace "
                f"({resolved}). Loading it executes arbitrary code — confirm "
                "provenance before pickle.load()/joblib.load()."
            )
        return findings

    if suffix != ".csv":
        return findings

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings

    hidden = find_hidden_unicode(text[:20000])
    if hidden:
        codepoints = ", ".join(f"U+{ord(c):04X}" for c in sorted(hidden))
        findings.append(
            f"{path.name} contains hidden/bidi-override unicode characters "
            f"({codepoints}) — inspect before trusting rendered values."
        )

    header = text.splitlines()[0] if text else ""
    if SECRET_NAME_RE.search(header):
        findings.append(
            f"{path.name}'s header row looks like it names a secret (matched a "
            "key/password/token-like column name) — confirm this isn't real "
            "credential data before using it."
        )

    return findings


def extract_notebook_text(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name == "Edit":
        return tool_input.get("new_string", "")
    if tool_name == "MultiEdit":
        return "\n".join(e.get("new_string", "") for e in tool_input.get("edits", []))
    if tool_name == "NotebookEdit":
        return tool_input.get("new_source", "")
    return ""


def scan_notebook_edit(file_path: str, tool_name: str, tool_input: dict) -> list:
    findings = []
    if Path(file_path).suffix.lower() != ".ipynb":
        return findings

    text = extract_notebook_text(tool_name, tool_input)
    if not text:
        return findings

    if PICKLE_RE.search(text):
        findings.append(
            "This notebook edit calls pickle.load()/joblib.load() — confirm the "
            "source file is inside the project workspace and trusted before running "
            "this cell."
        )

    for line in text.splitlines():
        if SHELL_MAGIC_RE.match(line):
            findings.append(
                f"Shell magic in notebook cell ('{line.strip()[:60]}') — review "
                "before executing."
            )
            break

    hidden = find_hidden_unicode(text)
    if hidden:
        codepoints = ", ".join(f"U+{ord(c):04X}" for c in sorted(hidden))
        findings.append(
            f"Notebook content contains hidden/bidi-override unicode characters "
            f"({codepoints}) — inspect before trusting the rendered cell."
        )

    if SECRET_VALUE_RE.search(text) or SECRET_NAME_RE.search(text):
        findings.append(
            "Notebook content contains a secret-looking name or value (key/password/"
            "token pattern, or a long hex/base64-like string) — confirm it isn't "
            "a real credential before committing."
        )

    return findings


def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    cwd = payload.get("cwd", "")
    file_path = tool_input.get("file_path", "")

    findings = []
    if tool_name == "Read" and file_path:
        findings = scan_read(file_path, cwd)
    elif tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit") and file_path:
        findings = scan_notebook_edit(file_path, tool_name, tool_input)

    if findings:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    "last-ds-mile safety scan (warn-only, not blocking):\n- "
                    + "\n- ".join(findings)
                ),
            }
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()
