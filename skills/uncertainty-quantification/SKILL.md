---
name: uncertainty-quantification
description: Reports every metric with its variance across folds/seeds instead of a bare point estimate, and states whether a model-vs-baseline or model-vs-model gap is larger than that variance. Use during /ds-model or /ds-evaluate when comparing scores, or whenever two numbers are being called "different" or "consistent" without a spread to back that up.
---

# uncertainty-quantification

## Overview

A single cross-validated score is a sample from a distribution, not the truth. Two
numbers that differ by less than the fold-to-fold noise are the same number wearing
different digits. This skill exists so this plugin's own numbers don't commit the exact
over-claiming sin the rest of it exists to catch.

## When to Use

- Reporting any CV or resampled score in `/ds-model` or `/ds-evaluate`.
- Comparing a candidate model's score to the baseline, to another candidate, or to a
  score from a different validation scheme (e.g. CV vs. a temporal holdout) — the "is
  this real lift or noise" question.
- NOT for: choosing the split strategy itself (see `validation-strategy`) — this skill
  quantifies the noise *in* whatever split was chosen, it doesn't choose the split.

## Core Process

1. Never report a single fold's score as "the" score. Report the mean **and** the
   standard deviation (or a percentile interval) across folds — `cross_val_score`
   already returns per-fold values; use them, don't collapse to `.mean()` alone.
2. If the dataset is small (roughly under a few thousand rows) or the metric is noisy
   by nature (e.g. AUC on a rare positive class), repeat the CV with several different
   `random_state` seeds and pool the spread across repeats, not just across folds —
   fold variance alone understates the true uncertainty on small data.
3. Before calling one score "better than," "worse than," or "consistent with" another,
   compare the *gap* between them to the *spread* of each. A gap smaller than roughly
   one standard deviation is not a demonstrated difference — say so explicitly rather
   than picking the higher number and moving on.
4. State uncertainty in the same units as the metric everywhere it's reported — in the
   experiments table in `/ds-model`, and in the final number in `/ds-evaluate` — not as
   a caveat added only in one place and dropped elsewhere.
5. For a held-out temporal or sealed check performed once (not part of the CV loop),
   don't manufacture a fake standard deviation from n=1 — say plainly that it's a
   single point estimate with no variance, and treat any comparison to the CV mean as
   directional evidence only, not a statistical test.

## Techniques/Patterns

| Situation | Technique |
|---|---|
| Standard k-fold CV | Report `mean ± std` across the `k` fold scores, not just the mean |
| Small dataset (CV alone looks noisy) | Repeated k-fold (e.g. 5×5) with different seeds; pool all repeat×fold scores before computing mean/std |
| Comparing two models on the *same* folds | Paired difference per fold (`score_a[i] - score_b[i]`), then look at whether that paired difference's mean is consistently on one side of zero — much more sensitive than comparing two independent means |
| Comparing two models on *different* splits (e.g. one used nested CV, one didn't) | Don't compare the raw numbers directly — mismatched validation schemes produce mismatched noise profiles; note this explicitly instead of implying a fair comparison |
| Bootstrap CI on a single held-out set | Resample the held set with replacement (e.g. 1000x), recompute the metric each time, report the 2.5th/97.5th percentile as the interval |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The mean is higher, so this model is better" | Only if the gap exceeds the noise. A 0.001 AUC improvement with a 0.02 fold std is not a finding. |
| "Reporting a spread is more rigorous than this project needs" | It costs one extra line (`cross_val_score` already returns per-fold values) and it's the only thing standing between "the model improved" and "the model got lucky on these folds." |
| "The three schemes gave similar numbers, so the model generalizes" | "Similar" needs a number attached — similar relative to what spread? Without it, "similar" and "identical" are indistinguishable claims. |

## Red Flags

| Red Flag | What it usually means |
|---|---|
| A model comparison states one score is "better" with no spread reported for either | Exactly the gap this skill exists to close — go back and compute the per-fold spread before claiming a winner. |
| Two scores from different validation schemes (e.g. CV mean vs. a one-time temporal holdout) are called "consistent" | A single point estimate has no variance to be consistent *with* — restate as directional agreement, not statistical agreement. |

See `ds-method`'s Red Flags — "validation metric beats the training metric" is also
worth re-checking against fold spread, not just a single pair of numbers.

## Verification

- [ ] Every reported CV score includes a spread (std across folds, or across
      repeated-CV repeats), not a bare mean.
- [ ] Every model-vs-baseline or model-vs-model comparison states whether the gap
      exceeds the spread, not just which number is higher.
- [ ] A one-time holdout score (temporal, sealed) is never presented with a fabricated
      standard deviation, and its comparison to a CV mean is labeled directional, not
      statistical.
