---
name: ds-evaluate
description: Evaluates the chosen model on metrics aligned to the /ds-frame decision, including calibration and slice/subgroup performance, not just one aggregate leaderboard number. Use after modeling, before writing conclusions or a report.
---

# ds-evaluate — Evaluation & Error Analysis

## Overview

Produces the full evidence picture for the chosen model: the decision-aligned metric,
calibration, subgroup performance, and where it fails — not a single leaderboard number.

## When to Use

- After `/ds-model` has produced a best candidate.
- Before writing conclusions or a stakeholder report.
- NOT for: writing the stakeholder narrative itself (that's `/ds-report`) — this stage
  produces the evidence `/ds-report` is required to draw on.

## Core Process

1. Re-confirm the metric being reported is the one chosen in `/ds-frame`, not a
   different, more flattering metric picked after the fact.
2. Check calibration where relevant (predicted probabilities vs. observed frequencies),
   not only discrimination (e.g. AUC).
3. Slice performance by meaningful subgroups (segment, time period, geography, or
   whatever the decision depends on) — a single aggregate number can hide a subgroup
   where the model fails badly.
4. Run error analysis: look at the worst mispredictions and look for a pattern.
5. Export the slice-performance comparison (bar chart of the metric per subgroup, always
   against the overall number so the gap is visible) and, for a probabilistic
   classifier, the calibration curve (predicted-decile vs. actual-rate) as figures to
   `.last-ds-mile/figures/07-<name>.png` — per `data-viz-standards`. These are the two
   plots this stage's own findings are least readable as prose.
6. Write to `.last-ds-mile/stages/07-evaluate.md`: the aggregate metric, the calibration
   check, the slice table, error-analysis notes, and a reference to each exported figure.

**If this project went through the Sealed Bet (`/ds-seal` → `/ds-auto`/`/ds-model` →
`/ds-open`):** steps 2–4 need the true held-set labels, which are off-limits until
`/ds-open` has run. Once it has, `open_seal()` has already called
`sealed_bet.score.reveal()`, which writes `held/revealed.csv` (the true target plus the
submitted predictions) — join it with the already-readable `held/features.csv` by row
order to get everything this stage needs. Never read `held/_sealed_target.csv` directly
(it's guard-blocked for exactly this reason, and reading it through a workaround — a
shell command, a script, anything other than `held/revealed.csv` — defeats the point of
the guard even if it isn't literally intercepted). If `held/revealed.csv` doesn't exist
yet, the seal hasn't been opened — stop and run `/ds-open` first, don't work around it.

## Common Rationalizations

See `ds-method` for the shared Rationalizations that apply to every stage, in particular
"one aggregate metric is enough to report" — this stage exists specifically to prevent
that shortcut from reaching `/ds-report`.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| The overall metric is good but was never checked per-slice | This is exactly the condition `/ds-report`'s Hard Gate checks for — resolve it here, not there. |

See `ds-method` for the shared Red Flags that apply to every stage.

## Verification

- [ ] The metric reported is the one chosen in `/ds-frame`, not a substituted one.
- [ ] Calibration checked where the problem type makes it relevant.
- [ ] A slice/subgroup performance table exists, not only an aggregate number.
- [ ] Error analysis performed on the worst mispredictions.
- [ ] Slice-performance (and, if classification, calibration) exported as a figure to
      `.last-ds-mile/figures/`, not only a table in prose.
- [ ] `.last-ds-mile/stages/07-evaluate.md` written.
