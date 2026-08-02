---
name: ds-validate
description: Chooses a leakage-safe way to split data — temporal, grouped, stratified, or nested cross-validation — matched to how the rows are actually structured, and decided before any model is trained. Use when someone asks how to split into train and test, set up cross-validation, or pick between KFold, GroupKFold, StratifiedKFold, and TimeSeriesSplit. Use when repeated entities, time ordering, or nesting could make a random split leak. Use when tuning hyperparameters without contaminating the test set.
---

# ds-validate — Validation Design

## Overview

Decides how the data will be split for honest evaluation, driven by the data's actual
structure (time, groups, imbalance) rather than by whatever split is easiest to code.

## When to Use

- Before `/ds-model` — this is a Hard Gate `/ds-model` checks for.
- Whenever asked to set up train/test splits or cross-validation.
- NOT for: picking which model to try (that's `/ds-model`) — this stage fixes the split
  strategy first so it can't later be tuned to flatter a specific model.

## Core Process

1. Ask: is there a time dimension where future data could leak into past predictions?
   If yes, use a temporal split or backtesting scheme — never shuffled cross-validation.
2. Ask: are there groups (e.g. the same customer or patient across multiple rows) that
   must not span both train and validation? If yes, use grouped cross-validation (e.g.
   `GroupKFold`).
3. Ask: is the target imbalanced? If yes, use stratified splits so folds preserve class
   balance.
4. Ask: is there a fixed test set (Kaggle-style) or a known deployment population this
   model will actually be scored against? If yes, run adversarial validation between
   training data and that population before finalizing the split — see
   `distribution-shift`. A split that looks fine internally can still fail to predict
   real transfer if the test/production distribution differs from training.
5. If none of the above apply, plain (or stratified) k-fold is fine — state that
   explicitly rather than choosing it by default without checking.
6. Implement with the sklearn splitter that matches the answer — don't hand-roll a split
   when a splitter class already exists for the case. See the reference table below.
7. Write to `.last-ds-mile/stages/05-validate.md`: the chosen strategy, why, the
   distribution-shift check and its result, and the exact split/CV code to be reused
   identically in `/ds-model`.

## Splitter reference

| Situation | sklearn splitter | Notes |
|---|---|---|
| No time/group/imbalance concern | `KFold(shuffle=True)` | Always set `random_state` for reproducibility |
| Imbalanced classification target | `StratifiedKFold` | Preserves class ratio per fold |
| Imbalanced regression target | `StratifiedKFold` on `pd.qcut(target, q=5)` bins | Standard workaround — sklearn has no native regression-stratified splitter |
| Repeated entity (customer/patient/house) across rows | `GroupKFold` | Prevents the same entity's rows spanning train and validation |
| Both grouped AND imbalanced | `StratifiedGroupKFold` | Only in sklearn ≥1.1 |
| Time-ordered data | `TimeSeriesSplit`, or a manual expanding/rolling window | Never shuffle; always train-on-past, evaluate-on-future |

## Nested CV — when a single validation split isn't enough

If model selection involves tuning hyperparameters (not just training one fixed model),
evaluating the *tuned* model on the same validation split used to pick those
hyperparameters gives an optimistic estimate — the validation score has now been "seen"
by the tuning process. **Nested CV** fixes this with two loops:

- **Outer loop**: splits data into outer-train / outer-test, for the final unbiased
  performance estimate.
- **Inner loop**: runs *inside* each outer-train fold, splitting further to search
  hyperparameters (e.g. via `GridSearchCV`) — the outer-test fold is never touched by
  the inner loop.

Use nested CV when the dataset is small enough that a single held-out validation set
would be noisy, AND real hyperparameter tuning (not just trying 2-3 fixed models) is
happening. Skip it when the dataset is large enough that a single validation split is
already low-variance, or when only comparing a handful of fixed-hyperparameter models —
that's plain CV, not nested.

```python
from sklearn.model_selection import GridSearchCV, KFold, cross_val_score

# inner_cv tunes hyperparameters; outer_cv gives the honest final estimate
inner_cv = KFold(n_splits=3, shuffle=True, random_state=0)
outer_cv = KFold(n_splits=5, shuffle=True, random_state=1)

search = GridSearchCV(estimator, param_grid, cv=inner_cv)
nested_scores = cross_val_score(search, X, y, cv=outer_cv)
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I already tuned hyperparameters with plain CV, nested CV is overkill" | It depends on dataset size, not effort already spent — a small, noisy dataset needs the outer loop regardless of how much tuning already happened. |

See `ds-method` for the shared Rationalizations that apply to every stage, in particular
"I'll pick the validation strategy after I see how the data looks in modeling" — that is
exactly the rationalization this stage exists to prevent.

## Red Flags

See `ds-method`'s Red Flags — in particular, "validation metric beats the training
metric" is this stage's clearest signal of a broken or shuffled temporal split.

See `lessons/the-leaderboard-that-lied.md` for a real example of this exact
failure mode.

## Verification

- [ ] Time, group, imbalance, and distribution-shift questions all answered
      explicitly, not skipped.
- [ ] Chosen strategy documented with its justification.
- [ ] The chosen splitter matches the data's actual structure, not the easiest one
      to code.
- [ ] If hyperparameters were tuned, the final reported score comes from an outer loop
      the tuning process never saw.
- [ ] `random_state` is set and recorded for every splitter used.
- [ ] Exact split/CV code recorded for identical reuse in `/ds-model`.
- [ ] `.last-ds-mile/stages/05-validate.md` written.
