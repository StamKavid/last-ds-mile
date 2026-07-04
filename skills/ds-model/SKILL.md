---
name: ds-model
description: Selects and tunes models against the validation strategy from /ds-validate, always compared to the /ds-baseline anchor. Hard gate — refuses to proceed without both a prior baseline and a documented validation strategy. Use when asked to train, tune, or compare models.
---

# ds-model — Modeling

## Overview

Trains and compares candidate models strictly against the validation strategy and
baseline established in the two prior stages — never against an ad hoc split invented on
the spot.

## When to Use

- After `/ds-baseline` and `/ds-validate` have both produced their artifacts.
- Whenever asked to train, tune, or compare models.
- NOT for: deciding the final metrics story or slice performance (that's
  `/ds-evaluate`) — this stage picks the best candidate, evaluation happens next.

## Core Process

1. **Gate check:** confirm `.last-ds-mile/stages/04-baseline.md` and
   `.last-ds-mile/stages/05-validate.md` both exist. If either is missing, stop and tell
   the user to run `/ds-baseline` or `/ds-validate` first — do not proceed by inventing
   an ad hoc split or skipping the comparison.
2. Train candidate models using the exact validation strategy from `/ds-validate` — the
   same split/CV code, not a rewritten version.
3. Track each experiment's configuration and score. A plain markdown table is sufficient
   at this scale; a full experiment-tracking tool is optional, not required.
4. Compare every candidate explicitly to the baseline score from `/ds-baseline`. State
   the lift (or lack of it) plainly, in the same units as the metric.
5. Write to `.last-ds-mile/stages/06-model.md`: the experiments table, the best
   candidate, and its lift over baseline.

## Common Rationalizations

See `ds-method` for the shared Rationalizations that apply to every stage, in particular
"I'll just peek at the test set once" — the temptation is strongest exactly at this
stage, during tuning.

## Red Flags

See `ds-method`'s Red Flags, in particular "metric looks too good on the first try" —
the single most common signal that something upstream (usually in `/ds-prep`) leaked.

## Verification

- [ ] Gate check passed: both `.last-ds-mile/stages/04-baseline.md` and
      `.last-ds-mile/stages/05-validate.md` exist and were read before modeling began.
- [ ] The same validation code from `/ds-validate` was reused, not rewritten.
- [ ] Every candidate model is compared to the baseline score explicitly.
- [ ] `.last-ds-mile/stages/06-model.md` written.
