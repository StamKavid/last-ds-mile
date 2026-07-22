---
name: ds-explain
description: Interprets the model — permutation feature importance, SHAP values, and (for an ensemble) a cross-check against its best single base learner — to sanity-check that it learned sensible drivers rather than an artifact. Use after evaluation, before reporting results to stakeholders.
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

1. Compute permutation feature importance for the chosen model on the held set.
2. Compute SHAP values (not just permutation importance — magnitude alone doesn't show
   *direction*, and direction is what catches a feature that's technically predictive
   but for a nonsensical or leaked reason). If the winning model is a black-box ensemble
   (AutoGluon, stacked/blended), explain the ensemble's actual `predict`/`predict_proba`
   as a callable via `shap.Explainer` rather than reaching into a specific base learner's
   internals — an individual base model's own preprocessing is often fragile/internal
   API and version-specific to access directly, and explaining the real predict function
   is both simpler and more honest about what actually ships. Encode any categorical
   columns numerically first (e.g. `sklearn.preprocessing.OrdinalEncoder`) with a
   decode step inside the wrapped predict function — SHAP's default tabular masker
   assumes numeric arrays. A background sample of ~20-30 dev rows and explaining
   ~50-60 held rows is enough for a summary plot; this doesn't need to run on every row.
3. If the winning model is an ensemble over multiple base model types (e.g. AutoGluon's
   CatBoost/LightGBM/RandomForest), also compute permutation importance for the single
   best-scoring base model (not just the ensemble) and compare rankings. Agreement is
   reassuring; a feature that matters to the ensemble but not to any individual base
   model (or vice versa) is worth a sentence — it's a real finding about how the
   ensemble blends signal, not noise to average away.
4. Check the top features against domain expectations: do they make sense as drivers, or
   does a suspicious feature dominate — a leakage signal that slipped past `/ds-prep`?
5. If a feature's importance is implausibly high, stop and re-check it against the
   `/ds-prep` known-at-prediction-time list before proceeding to `/ds-report`.
6. **Word every finding as predictive, not causal, unless a causal identification
   strategy is stated** (see `causal-vs-predictive`) — "X is associated with Y," not
   "X reduces/causes/drives Y," especially for any feature the subject chose
   themselves (a contract, a plan tier, an opt-in), where self-selection is the
   obvious confound.
7. Export the permutation importance (ensemble, and the base-model cross-check if step 3
   applies) and the SHAP summary (beeswarm) as figures to
   `.last-ds-mile/figures/08-<name>.png`.
8. Write to `.last-ds-mile/stages/08-explain.md`: the importance ranking, the SHAP
   finding, any base-model cross-check finding, sanity commentary, any features sent
   back for a leakage re-check, and a reference to each exported figure.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The model works, I don't need to know why" | Working on this dataset doesn't mean it will work in production if the driver is an artifact of how this dataset happened to be built. |

See `ds-method` for the shared Rationalizations that apply to every stage.

See `causal-vs-predictive` for the Rationalizations specific to mistaking a strong
predictive driver for a causal one.

## Red Flags

See `ds-method`'s Red Flags — in particular, "a single feature has near-perfect
importance" is exactly what this stage exists to catch.

See `causal-vs-predictive`'s Red Flags — a driver the subject chose themselves
(a contract, a plan, an opt-in) described as "reducing" or "causing" the outcome
without a self-selection argument is this stage's other common failure mode.

See `lessons/the-contract-that-wasnt-the-cause.md` for a real example.

## Verification

- [ ] Permutation feature importance computed for the chosen model.
- [ ] SHAP values computed and a summary plot exported — not skipped as "importance is
      enough."
- [ ] If the winner is a multi-base-model ensemble, importance cross-checked against its
      best single base learner, and any disagreement noted.
- [ ] Top drivers checked against domain expectations, not accepted uncritically.
- [ ] Any implausible driver re-checked against `/ds-prep`'s known-at-prediction-time
      list.
- [ ] Every driver finding is worded as predictive/associational unless a causal
      identification strategy is stated (see `causal-vs-predictive`).
- [ ] Figures exported to `.last-ds-mile/figures/`, not only tables in prose.
- [ ] `.last-ds-mile/stages/08-explain.md` written.
