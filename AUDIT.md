# AUDIT.md — What This Plugin's Hooks Actually Do

Last DS Mile ships four hooks (see `hooks/hooks.json`). This file exists because an
agent plugin that touches your data and notebooks should be auditable by design, not
because you asked. Every hook here is a short, readable script with **zero network
calls** and no dependencies beyond the Python 3 standard library. Read them
yourself — that's the point.

## Hooks

| Hook | File | Reads | Writes | Network |
|---|---|---|---|---|
| `SessionStart` | `hooks/session_start.py` | `.last-ds-mile/stages/*.md` (filenames only), `.last-ds-mile/learnings.jsonl` (line count only) | nothing | none |
| `PostToolUse` | `hooks/scan_untrusted_input.py` | the file just read or edited (`tool_input.file_path`), bounded to `.csv`/`.parquet`/`.xlsx`/`.pkl`/`.joblib` on Read and `.ipynb` on Edit/Write/MultiEdit/NotebookEdit | nothing | none |
| `PreCompact` | `hooks/pre_compact.py` | `.last-ds-mile/stages/*.md` (filenames only) | `.last-ds-mile/session-state.json` | none |
| `Stop` | `hooks/stop_persist_learnings.py` | `.last-ds-mile/stages/*.md` (filenames only) | appends one line to `.last-ds-mile/learnings.jsonl` | none |

All four hooks are invoked through one shared wrapper, `hooks/ds-python.sh` — a
short bash script that finds a working Python 3 interpreter (`python3`, `python`,
or `py -3`, in that order) and execs the target hook script through it. It exists
to work around a Windows/Git Bash quirk (the Microsoft Store's `python3` stub) and
a related path-form mismatch. It reads and writes nothing itself, makes no network
calls, and its only job is picking an interpreter and handing off — read it
alongside the 4 hook scripts if you want the complete picture of what actually runs.

All four exit 0 unconditionally — **warn, don't block** is the default posture (see
the project's design doc for the full rationale). Filesystem writes (`PreCompact` and
`Stop`) are wrapped in error handling so a filesystem surprise (permissions, a path
collision) degrades to a silent no-op rather than crashing the hook. None of the
hooks read file *contents* except `scan_untrusted_input.py`, which reads only the
specific file the agent just touched (never a directory sweep) and only to look for
the patterns below — it never sends that content anywhere; it only prints a short
warning string back to Claude Code via `hookSpecificOutput.additionalContext`.

To verify the no-network and stdlib-only claims yourself: `grep -n "^import\|^from" hooks/*.py` shows every import (all four hooks use only `json`, `sys`, `re`, `pathlib`, `datetime`) and `grep -rniE "requests\.|urllib|socket\.|http\.client|\.urlopen\(" hooks/*.py` should return nothing.

## What `scan_untrusted_input.py` looks for

- **Pickle/joblib files read from outside the project workspace** — loading them
  executes arbitrary code; this is one of the highest-severity risks in the DS
  stack. If the hook can't determine the project workspace at all (no `cwd` in the
  payload), it warns that provenance is unknown rather than staying silent.
- **Hidden/bidi-override unicode characters** (zero-width spaces, bidi embedding and
  override marks) in CSV content or notebook edits — the same trick used to hide
  prompt-injection payloads in text that looks empty or differently-ordered than it
  renders.
- **`pickle.load()`/`joblib.load()` calls appearing in a notebook edit** — flagged so
  you confirm the source path before running the cell.
- **Shell magics (`!...`) in a notebook cell** — flagged for review, not blocked.
- **Secret-looking column names or values** (`api_key`, `password`, `token`, or a long
  hex/base64-looking string) — flagged so you don't accidentally commit real
  credentials that ended up in a data file. On CSVs read directly, this check only
  looks at the header row's column *names*, not every row's values (a full per-row
  scan is out of scope for a fast PostToolUse hook); notebook edits get a broader
  check across the full edited text, including value-shaped patterns.

## Recommended permission baseline

`settings-baseline.json` at the repo root is a documented, opt-in fragment for your
own project's `.claude/settings.json` — this plugin never modifies your settings
automatically. See the README's "Safety" section for how to adopt it.

## Subagents

`leakage-auditor` (opus), `ds-reviewer` (sonnet), and `data-profiler` (haiku) — see
`agents/`. Like all Claude Code subagents, they call the Claude API to reason and use
only the standard tool set; they read no files and make no network calls beyond that.
