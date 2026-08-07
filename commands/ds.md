---
description: Show the Last DS Mile pipeline map and which stage comes next
---

Check `.last-ds-mile/stages/` in the current project for existing stage output files
(`00-frame.md` through `12-deploy.md`). Use the Glob tool on `.last-ds-mile/stages/*.md`
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
    11. /ds-package   Package + training/serving parity check
    12. /ds-deploy    Local endpoint + monitoring, drift, rollback

Stages 3–7 are not strictly linear: `/ds-iterate` reads `/ds-evaluate`'s findings after
every pass and either routes back to `/ds-prep`, `/ds-validate`, or `/ds-model` with a
named diagnosis, or confirms the result is ready to proceed. Don't treat one pass
through 3–7 as automatically done — check whether `.last-ds-mile/stages/07-iterate-log.md`
exists and has a "proceed" verdict before recommending `/ds-explain`.

**This command shows the map and stops. That is its whole job.**

It is a status answer to "where do I stand", nothing more. If `.last-ds-mile/stages/`
doesn't exist yet, print the map, recommend `/ds-frame` as the first move, and explain
that each stage's output feeds the next. If stages exist, print the map and name the
first missing one.

Never route a task through this command. A request to build, evaluate, or ship a
model belongs to the `data-science-project` skill, which carries it to a result in the
same turn — reaching this map mid-task and stopping to ask which stage to start at is a
measured failure, not a hypothetical one: in a two-arm eval it cost two of three trials
their verdict entirely, while the unaided model simply answered. If you are carrying out
a task and find yourself here, you took a wrong turn: go back to `data-science-project`
and do the work.

When recommending the next stage: name the command matching the first missing stage in
order. If the user asks to skip ahead to `/ds-model`, `/ds-report`,
`/ds-handoff`, `/ds-package`, or `/ds-deploy` without the stages before it, apply
`ds-method`'s Hard Gate handling: discipline gates (baseline, validation, slice
performance, pinned environment) get produced inline so the task still completes;
safety gates (`/ds-package`'s parity check, `/ds-deploy`'s monitoring/rollback) stop and
ask, since those are irreversible or externally visible. If `/ds-evaluate` exists but
`/ds-iterate` hasn't run yet, recommend `/ds-iterate` next, not `/ds-explain`.
