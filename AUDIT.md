# AUDIT.md — What This Plugin's Hooks Actually Do

Last DS Mile ships five hooks (see `hooks/hooks.json`). This file exists because an
agent plugin that touches your data and notebooks should be auditable by design, not
because you asked. Every hook here is a short, readable script with **zero network
calls** and no dependencies beyond the Python 3 standard library. Read them
yourself — that's the point.

## Hooks

| Hook | File | Reads | Writes | Network |
|---|---|---|---|---|
| `SessionStart` | `hooks/session_start.py` | `.last-ds-mile/stages/*.md` (filenames only), `.last-ds-mile/learnings.jsonl` (full content — parses `type`/`tags`/`title` fields per line, not just a line count), the plugin's own `lessons/*.md` frontmatter (`title`/`stages` fields only, via a stdlib regex parser — never the lesson body text) | nothing | none |
| `PreToolUse` | `hooks/seal_guard.py` | only the `tool_input.file_path` string on `Read` calls — opens no files | nothing | none |
| `PostToolUse` | `hooks/scan_untrusted_input.py` | the file just read or edited (`tool_input.file_path`), bounded to `.csv`/`.parquet`/`.xlsx`/`.pkl`/`.joblib` on Read and `.ipynb` on Edit/Write/MultiEdit/NotebookEdit | nothing | none |
| `PreCompact` | `hooks/pre_compact.py` | `.last-ds-mile/stages/*.md` (filenames only) | `.last-ds-mile/session-state.json` | none |
| `Stop` | `hooks/stop_persist_learnings.py` | `.last-ds-mile/stages/*.md` (filenames only) | appends one line to `.last-ds-mile/learnings.jsonl` | none |

All five hooks are invoked through one shared wrapper, `hooks/ds-python.sh` — a
short bash script that finds a working Python 3 interpreter (`python3`, `python`,
or `py -3`, in that order) and execs the target hook script through it. It exists
to work around a Windows/Git Bash quirk (the Microsoft Store's `python3` stub) and
a related path-form mismatch. It reads and writes nothing itself, makes no network
calls, and its only job is picking an interpreter and handing off — read it
alongside the 5 hook scripts if you want the complete picture of what actually runs.

All five exit 0 unconditionally — **warn, don't block** is the default posture for
four of them (see the project's design doc for the full rationale). `seal_guard.py`
is the one deliberate exception: it still exits 0, but it can return a
`permissionDecision: "deny"` in its JSON output, which is Claude Code's mechanism
for actually blocking a tool call rather than just annotating it — see the
dedicated section below. Filesystem writes (`PreCompact` and
`Stop`) are wrapped in error handling so a filesystem surprise (permissions, a path
collision) degrades to a silent no-op rather than crashing the hook. `SessionStart`'s
read of `learnings.jsonl` is similarly guarded — an unreadable file (permissions, or
the path being a directory) degrades to an honest "present but unreadable" status
string rather than crashing. Only `scan_untrusted_input.py` and `SessionStart` read file *contents* —
`scan_untrusted_input.py` reads only the specific file the agent just touched
(never a directory sweep) and only to look for the patterns below;
`SessionStart` reads `learnings.jsonl` and the plugin's own `lessons/*.md`
frontmatter (see the table above) only to compute the relevant-lessons
summary. Neither sends that content anywhere — they only print a short
context string back to Claude Code via `hookSpecificOutput.additionalContext`.
`seal_guard.py` reads no file contents at all — it only pattern-matches the
path string from `tool_input.file_path`.

To verify the no-network and stdlib-only claims yourself: `grep -n "^import\|^from" hooks/*.py` shows every import (all five hooks use only `json`, `sys`, `re`, `pathlib`, `datetime`) and `grep -rniE "requests\.|urllib|socket\.|http\.client|\.urlopen\(" hooks/*.py` should return nothing.

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

### `seal_guard.py` (PreToolUse / Read)
- **Reads:** only the `tool_input.file_path` string from stdin. Opens no files.
- **Writes:** nothing.
- **Network:** none.
- **Blocks?** YES — the one intentionally blocking hook. Denies Read on any
  `_sealed*` file under a `held/` directory (the sealed holdout labels). Everything
  else, including `held/features.csv`, is allowed. This is the physical basis of
  the Sealed Bet trust guarantee, so it blocks rather than warns.
- **Known limitation (Phase A):** this hook only gates the `Read` tool. `Bash`,
  `Grep`, and any other tool that can surface file contents without going
  through Claude Code's `Read` tool are not currently gated — an agent could
  still `cat`/`Get-Content`/`grep` the sealed file directly and bypass this
  guard entirely. This is a documented gap, not a complete guarantee.
  Closing it requires parsing/canonicalizing arbitrary shell command strings
  (quoting, variable expansion, encoding, wildcards), which is its own
  substantial adversarial-hardening project and is out of scope here.

## Recommended permission baseline

`settings-baseline.json` at the repo root is a documented, opt-in fragment for your
own project's `.claude/settings.json` — this plugin never modifies your settings
automatically. See the README's "Safety" section for how to adopt it.

## Subagents

`leakage-auditor` (opus), `ds-reviewer` (sonnet), and `data-profiler` (haiku) — see
`agents/`. Like all Claude Code subagents, they call the Claude API to reason and use
only the standard tool set; they read no files and make no network calls beyond that.
