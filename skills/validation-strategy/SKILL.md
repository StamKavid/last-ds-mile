---
name: validation-strategy
description: Reference for choosing and implementing a cross-validation strategy — temporal, grouped, stratified, or nested — matched to the data's actual structure. Use when setting up train/validation splits, when deciding how to tune hyperparameters without leaking the test set, or when asked about K-fold, GroupKFold, TimeSeriesSplit, or nested CV.
---

# validation-strategy

## Overview

Goes deeper than `/ds-validate`'s per-project checklist: this is the technique
reference for the CV mechanics themselves, including nested CV for honest
hyperparameter tuning — the one case `/ds-validate`'s lightweight version doesn't
cover.

## When to Use

- Setting up any train/validation split or CV scheme, in or out of the `/ds-*`
  pipeline.
- Deciding whether hyperparameter tuning itself needs its own honest evaluation loop
  (nested CV).
- NOT for: picking a model or a metric (see `metric-selection`) — this skill is
  purely about the split mechanics.

## Core Process

1. Answer the same three structural questions as `/ds-validate` (time, groups,
   imbalance) if not already answered there.
2. If hyperparameters will be tuned (grid/random search, early stopping thresholds,
   etc.), decide whether a single validation split is enough or whether nested CV is
   needed (see the decision below).
3. Implement using the sklearn splitter that matches the answer — don't hand-roll a
   split when a splitter class already exists for the case.

## Techniques/Patterns

### Splitter reference

| Situation | sklearn splitter | Notes |
|---|---|---|
| No time/group/imbalance concern | `KFold(shuffle=True)` | Always set `random_state` for reproducibility |
| Imbalanced classification target | `StratifiedKFold` | Preserves class ratio per fold |
| Imbalanced regression target | `StratifiedKFold` on `pd.qcut(target, q=5)` bins | Standard workaround — sklearn has no native regression-stratified splitter |
| Repeated entity (customer/patient/house) across rows | `GroupKFold` | Prevents the same entity's rows spanning train and validation |
| Both grouped AND imbalanced | `StratifiedGroupKFold` | Only in sklearn ≥1.1 |
| Time-ordered data | `TimeSeriesSplit`, or a manual expanding/rolling window | Never shuffle; always train-on-past, evaluate-on-future |

### Nested CV — when a single validation split isn't enough

If model selection involves tuning hyperparameters (not just training one fixed
model), evaluating the *tuned* model on the same validation split used to pick those
hyperparameters gives an optimistic estimate — the validation score has now been
"seen" by the tuning process. **Nested CV** fixes this with two loops:

- **Outer loop**: splits data into outer-train / outer-test, for the final unbiased
  performance estimate.
- **Inner loop**: runs *inside* each outer-train fold, splitting further to search
  hyperparameters (e.g. via `GridSearchCV`) — the outer-test fold is never touched by
  the inner loop.

Use nested CV when: the dataset is small enough that a single held-out validation set
would be noisy, AND real hyperparameter tuning (not just trying 2-3 fixed models) is
happening. Skip it when: the dataset is large enough that a single validation split is
already low-variance, or when only comparing a handful of fixed-hyperparameter models
(that's plain CV, not nested).

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

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

See `ds-method`'s Red Flags — "validation metric beats the training metric" and
"test set touched during hyperparameter search" are this skill's primary triggers.

## Verification

- [ ] The chosen splitter matches the data's actual time/group/imbalance structure,
      not the easiest one to code.
- [ ] If hyperparameters were tuned, the final reported score comes from an outer
      loop the tuning process never saw.
- [ ] `random_state` is set and recorded for every splitter used.
