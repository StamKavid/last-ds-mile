---
description: Show the Last DS Mile pipeline map and route to the next stage
---

Check `.last-ds-mile/stages/` in the current project for existing stage output files
(`00-frame.md` through `10-handoff.md`). Use the Glob tool on `.last-ds-mile/stages/*.md`
to see what already exists.

Print the pipeline map below, marking each stage done (✓) if its file exists, or next
(→) for the first missing one in order:

    0.  /ds-frame     Problem framing
    1.  /ds-data      Data understanding
    2.  /ds-explore   EDA
    3.  /ds-prep      Cleaning + feature engineering  <─┐
    4.  /ds-baseline  Honest baseline                   │
    5.  /ds-validate  Validation design                 │  loop back
    6.  /ds-model     Modeling                        <─┤  (see /ds-iterate)
    7.  /ds-evaluate  Evaluation + error analysis    ───┘
    7½. /ds-iterate   Diagnose evaluate's findings, route back or proceed
    8.  /ds-explain   Interpretation
    9.  /ds-report    Communication
    10. /ds-handoff   Reproducibility & handoff

Stages 3–7 are not strictly linear: `/ds-iterate` reads `/ds-evaluate`'s findings after
every pass and either routes back to `/ds-prep`, `/ds-validate`, or `/ds-model` with a
named diagnosis, or confirms the result is ready to proceed. Don't treat one pass
through 3–7 as automatically done — check whether `.last-ds-mile/stages/07-iterate-log.md`
exists and has a "proceed" verdict before recommending `/ds-explain`.

If `.last-ds-mile/stages/` doesn't exist yet, recommend starting with `/ds-frame` and
explain that each stage's output feeds the next.

Otherwise, recommend the command matching the first missing stage in order. If the
user asks to skip ahead to `/ds-model`, `/ds-report`, or `/ds-handoff` without the
stages before it, remind them of that stage's Hard Gate (see `ds-method`) rather than
silently letting them skip it — a missing baseline or validation strategy is not
something to route around. If `/ds-evaluate` exists but `/ds-iterate` hasn't run yet,
recommend `/ds-iterate` next, not `/ds-explain`.
