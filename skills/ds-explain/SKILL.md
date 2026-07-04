---
name: ds-explain
description: Interprets the model — feature importance, SHAP values, or partial dependence — to sanity-check that it learned sensible drivers rather than an artifact. Use after evaluation, before reporting results to stakeholders.
---

# ds-explain — Interpretation

## Overview

Checks that the model's top drivers make sense, catching leakage or artifacts that
survived evaluation because they didn't hurt the metric.

## When to Use

- After `/ds-evaluate` has confirmed the model performs acceptably.
- Before `/ds-report` — a model that "works" for the wrong reason is a liability, not a
  win.
- NOT for: re-scoring the model (that's `/ds-evaluate`) — this stage explains, it
  doesn't re-measure performance.

## Core Process

1. Compute feature importance (or SHAP values for more nuanced attribution) for the
   chosen model.
2. Check the top features against domain expectations: do they make sense as drivers, or
   does a suspicious feature dominate — a leakage signal that slipped past `/ds-prep`?
3. If a feature's importance is implausibly high, stop and re-check it against the
   `/ds-prep` known-at-prediction-time list before proceeding to `/ds-report`.
4. Write to `.last-ds-mile/stages/08-explain.md`: the importance ranking, sanity
   commentary, and any features sent back for a leakage re-check.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The model works, I don't need to know why" | Working on this dataset doesn't mean it will work in production if the driver is an artifact of how this dataset happened to be built. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

See `ds-method`'s Red Flags — in particular, "a single feature has near-perfect
importance" is exactly what this stage exists to catch.

## Verification

- [ ] Feature importance or SHAP values computed for the chosen model.
- [ ] Top drivers checked against domain expectations, not accepted uncritically.
- [ ] Any implausible driver re-checked against `/ds-prep`'s known-at-prediction-time
      list.
- [ ] `.last-ds-mile/stages/08-explain.md` written.
