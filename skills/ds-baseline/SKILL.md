---
name: ds-baseline
description: Forces a dumb baseline (majority class, mean/median, or a single-rule heuristic) before any model is built, establishing the anchor metric everything else must beat. Use before /ds-model, or when asked to build or train a model and no baseline exists yet.
---

# ds-baseline — Honest Baseline

## Overview

Establishes the dumbest reasonable prediction as the anchor metric, so every later
model's score can be judged as real lift or noise, not judged in a vacuum.

## When to Use

- Before `/ds-model` — this is a Hard Gate `/ds-model` checks for.
- Whenever asked to build, train, or compare models and no baseline artifact exists yet
  for this problem.
- NOT for: tuning or comparing real candidate models (that's `/ds-model`) — this stage
  produces exactly one deliberately simple number to compare against.

## Core Process

1. Pick the simplest possible baseline for the problem type: mean or median prediction
   for regression; majority-class or prior-probability prediction for classification; or
   a simple rule already in informal use, if one exists.
2. Evaluate it using the exact success metric chosen in `/ds-frame` — not a different,
   more convenient metric.
3. Record the baseline score as the anchor. Every subsequent model must be compared
   against it, not against zero or against "feels better."
4. Write to `.last-ds-mile/stages/04-baseline.md`: the baseline definition, its score,
   and what "beating it" will concretely mean.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This is a well-known dataset/problem, everyone knows a baseline would be trivial" | Trivial to state is not the same as trivial to skip — it's the only thing that tells you whether your fancier model earned its added complexity. |

See `ds-method` for the shared Rationalizations that apply to every stage (including "the baseline is obviously worse, I'll skip it").

## Red Flags

See `ds-method`'s Red Flags — in particular, "model accuracy matches the majority-class
rate to 2 decimal places" is this stage's most direct signal that a later model isn't
actually beating the baseline.

## Verification

- [ ] Baseline defined and scored using the exact metric from `/ds-frame`.
- [ ] Baseline score recorded as the explicit comparison anchor for `/ds-model`.
- [ ] `.last-ds-mile/stages/04-baseline.md` written.
