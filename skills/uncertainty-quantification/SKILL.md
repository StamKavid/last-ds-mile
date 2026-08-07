---
name: uncertainty-quantification
description: Reports every score with its spread across folds or seeds, and says whether a gap between two numbers is bigger than that spread. Use when someone asks whether an improvement is real or just noise, or how confident to be that one model beats another. Use when two results are being called different or the same without a spread behind the claim.
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
- NOT for: choosing the split strategy itself (see `ds-validate`) — this skill
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
   compare the *gap* between them to the *spread* of each. A gap smaller than the fold
   standard deviation is not a demonstrated difference — say so explicitly rather than
   picking the higher number and moving on. Treat this as a **screening heuristic, not
   a test**: it is deliberately conservative, and the reason it can't be upgraded into
   a p-value is in "What fold spread can and cannot tell you" below.
4. State uncertainty in the same units as the metric everywhere it's reported — in the
   experiments table in `/ds-model`, and in the final number in `/ds-evaluate` — not as
   a caveat added only in one place and dropped elsewhere.
5. For a held-out temporal or sealed check performed once (not part of the CV loop),
   don't manufacture a fake standard deviation from n=1 — say plainly that it's a
   single point estimate with no variance, and treat any comparison to the CV mean as
   directional evidence only, not a statistical test.

## What fold spread can and cannot tell you

Be precise about what `mean ± std` across k folds is, because this skill is the one
everything else leans on when it says "exceeds the fold spread."

**The k fold scores are not independent observations.** With 5-fold CV, any two
training sets overlap in about 75% of their rows. That dependence means the usual
move — divide by `√k` to get a standard error, multiply by 1.96, call it a 95%
CI — is invalid here. Bengio & Grangier (2004) showed there is **no unbiased
estimator of the variance of k-fold CV**, so an interval built this way understates
the true uncertainty, sometimes badly. Report `mean ± std` as a *description of fold
variability*, not as a confidence interval, and don't attach a confidence level to it.

**This is why the step-3 bar uses the raw standard deviation rather than the standard
error.** The SD is roughly `√k` times wider than the (already-optimistic) SE, and that
extra width is doing real work — it is a rough offset for the dependence the SE
ignores. It buys a screening rule that is hard to fool, at the cost of sometimes
calling a real improvement "not demonstrated." For this plugin's purposes that
trade is the right one: the failure this guards against is shipping noise as a
finding, not missing a marginal gain.

**When you need an actual test, not a screen:**

| You want | Use |
|---|---|
| To compare two models properly on CV | Paired per-fold differences with the **corrected resampled t-test** (Nadeau & Bengio) — it inflates the variance term by `1/k + n_test/n_train` precisely to account for the overlap. The uncorrected paired t-test on fold scores has a badly inflated false-positive rate; don't use it. |
| A real confidence interval on the final number | Bootstrap the **held-out set** (below). One model, one fixed test set, resampled rows — the independence assumption actually holds. |
| To know if a difference survives seed noise | Repeated CV across seeds, then look at the distribution of the *paired difference*, not of each model's mean. |

Never report a CV-derived interval as though it were the held-out bootstrap interval.
They answer different questions: the first is "how much does this number move across
folds," the second is "how precisely do I know performance on this population."

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
