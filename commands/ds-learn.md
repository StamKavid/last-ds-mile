---
description: Capture a project-local lesson — what broke and what fixed it
argument-hint: "[what broke and what fixed it, or leave blank to be asked]"
---

Invoke the `capturing-learnings` skill now via the Skill tool to determine
whether what just happened clears the bar for a real lesson, and to get the
capture format. (This command's steps below are the mechanical write path;
`capturing-learnings`'s own Core Process covers the judgment call and also
fires as a standalone proactive nudge — the two lists overlap by design, not
by drift; keep them in sync if either changes.) Then:

1. If the user provided details in $ARGUMENTS, use them. Otherwise ask what
   broke and what fixed it.
2. Determine tags: always include the current or next pipeline stage
   (`ds-frame` through `ds-handoff`, from `.last-ds-mile/stages/` — same
   stage `/ds` would route to next) so the lesson can resurface via
   `SessionStart`'s stage-based matching, plus any domain skill(s)
   (`target-leakage-detection`, `imbalanced-data`, etc.) genuinely relevant.
   A skill-only tag with no stage tag will never resurface automatically —
   nothing in this plugin re-attaches a captured entry to a skill file, so
   always include a stage tag if you want this lesson to resurface.
3. Append one line to `.last-ds-mile/learnings.jsonl` (create the file and
   its parent `.last-ds-mile/` directory if either doesn't exist yet) with
   this exact shape:

```json
{"type": "lesson", "recorded_at": "<current UTC timestamp in the same format datetime.now(timezone.utc).isoformat() produces, e.g. 2026-07-10T14:23:45.123456+00:00 — matches what hooks/stop_persist_learnings.py already writes to this same file>", "session_id": "unknown", "title": "<short title>", "what_broke": "<the specific failure>", "what_fixed_it": "<the specific fix>", "tags": ["<stage-or-skill-name>", "..."]}
```

4. Confirm back to the user in one line: what was captured and which tags it
   was filed under.
