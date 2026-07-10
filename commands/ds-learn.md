---
description: Capture a project-local lesson — what broke and what fixed it
argument-hint: [what broke and what fixed it, or leave blank to be asked]
---

Invoke the `capturing-learnings` skill now via the Skill tool to determine
whether what just happened clears the bar for a real lesson, and to get the
capture format. Then:

1. If the user provided details in $ARGUMENTS, use them. Otherwise ask what
   broke and what fixed it.
2. Determine tags: which pipeline stage(s) (`ds-frame` through `ds-handoff`)
   and/or domain skill(s) this lesson is relevant to, from the current
   `.last-ds-mile/stages/` state and/or what the user names.
3. Append one line to `.last-ds-mile/learnings.jsonl` (create the file and
   its parent `.last-ds-mile/` directory if either doesn't exist yet) with
   this exact shape:

```json
{"type": "lesson", "recorded_at": "<current UTC ISO-8601 timestamp>", "session_id": "<session id if known, else \"unknown\">", "title": "<short title>", "what_broke": "<the specific failure>", "what_fixed_it": "<the specific fix>", "tags": ["<stage-or-skill-name>", "..."]}
```

4. Confirm back to the user in one line: what was captured and which tags it
   was filed under.
