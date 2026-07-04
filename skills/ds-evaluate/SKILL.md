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
5. Write to `.last-ds-mile/stages/07-evaluate.md`: the aggregate metric, the calibration
   check, the slice table, and error-analysis notes.

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
- [ ] `.last-ds-mile/stages/07-evaluate.md` written.
