---
name: imbalanced-data
description: Techniques for rare-positive or otherwise imbalanced targets — resampling, class weighting, threshold tuning, and metric choice. Use when a classification target has a minority class below roughly 20%, when accuracy looks high but the model never predicts the rare class, or when asked about SMOTE, class_weight, or oversampling.
---

# imbalanced-data

## Overview

A rare-positive target breaks the naive "just fit a classifier" approach in several
specific ways — this skill lists the fixes and, more importantly, where each one goes
wrong if applied carelessly.

## When to Use

- The target's minority class is well below 50% (a rough rule of thumb: under ~20%
  starts to matter, under ~5% matters a lot).
- Accuracy is high but the model's recall on the rare class is near zero.
- NOT for: choosing the reporting metric itself (see `metric-selection`, though the
  two overlap heavily) — this skill is about fitting the model, `metric-selection`
  is about scoring it.

## Core Process

1. Confirm the actual class balance (don't guess — `value_counts(normalize=True)`).
2. Pick one of the three fix categories below based on what the model/library
   supports, not habit.
3. If resampling (SMOTE, over/under-sampling), it must be fit inside each CV fold's
   training data only, never on the full dataset before splitting — same leakage
   rule as any other fit-requiring transform.
4. Re-check the metric choice (see `metric-selection`) — accuracy is almost never
   the right metric once the target is imbalanced.

## Techniques/Patterns

| Approach | When to prefer it | Leakage risk |
|---|---|---|
| `class_weight="balanced"` (or manual weights) | First thing to try — no data duplication, works with most sklearn estimators, no extra leakage surface | None — it's a loss-function change, not a data change |
| Oversampling minority class (random or SMOTE) | When the estimator doesn't support class weights, or oversampling empirically helps | High if fit on the full dataset — SMOTE synthesizes new points *from* the training data, so it must run inside the CV fold, after the split, never before |
| Undersampling majority class | Very large datasets where discarding majority-class rows doesn't hurt signal | Same as oversampling — undersample only within the training fold |
| Threshold tuning (move the decision threshold away from 0.5) | Whenever the model outputs a probability and the actual deployment decision has an asymmetric cost (see `metric-selection`) | None — this happens after prediction, doesn't touch training data |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll SMOTE the whole dataset once, then split for CV" | This is the single most common imbalanced-data leak: SMOTE-then-split lets synthetic points derived from validation-fold neighbors appear in the training fold. Always split first, then resample only the training portion, per fold. |
| "Accuracy went up, so the imbalance fix worked" | With severe imbalance, accuracy can stay high even if the model predicts the majority class 100% of the time. Check recall/precision on the minority class directly (see `metric-selection`). |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| Model recall on the minority class is 0% or near it, despite "good" accuracy | The model is predicting the majority class almost universally — an unfixed imbalance problem hiding behind a misleading metric |

See `ds-method`'s Red Flags — "model accuracy matches the majority-class rate to 2
decimal places" is directly this failure mode.

See `lessons/the-99-percent-fraud-model.md` for a real example of this exact
failure mode.

See `lessons/the-imbalance-knob-that-broke-silently.md` for a real example of a
library-specific imbalance-weighting parameter collapsing at an extreme ratio — a
different failure mode than a wrong metric, worth checking for separately.

## Verification

- [ ] Actual class balance measured and stated (not assumed).
- [ ] If resampling was used, it happened strictly inside each training fold, never
      before the split.
- [ ] The reporting metric was re-checked against `metric-selection`, not left as
      plain accuracy.
