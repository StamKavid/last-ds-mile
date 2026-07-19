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
    3.  /ds-prep      Cleaning + feature engineering
    4.  /ds-baseline  Honest baseline
    5.  /ds-validate  Validation design
    6.  /ds-model     Modeling
    7.  /ds-evaluate  Evaluation + error analysis
    8.  /ds-explain   Interpretation
    9.  /ds-report    Communication
    10. /ds-handoff   Reproducibility & handoff

If `.last-ds-mile/stages/` doesn't exist yet, recommend starting with `/ds-frame` and
explain that each stage's output feeds the next.

Otherwise, recommend the command matching the first missing stage in order. If the
user asks to skip ahead to `/ds-model`, `/ds-report`, or `/ds-handoff` without the
stages before it, remind them of that stage's Hard Gate (see `ds-method`) rather than
silently letting them skip it — a missing baseline or validation strategy is not
something to route around.
