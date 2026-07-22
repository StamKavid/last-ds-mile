---
name: distribution-shift
description: Checks whether the training distribution actually resembles the deployment (or Kaggle test-set) distribution — via adversarial validation and per-feature drift checks — rather than assuming a good CV score transfers. Use during /ds-validate before choosing a split, and again in /ds-evaluate when a model that scored well in CV underperforms on held-out or production data.
---

# distribution-shift

## Overview

A validation split only tells you the model generalizes *within* the training
distribution. It says nothing about whether that distribution matches where the model
will actually be scored — a future time period, a different population, or a Kaggle
test set collected slightly differently from train. This is the question
`/ds-validate`'s time/group/imbalance checklist doesn't ask.

## When to Use

- During `/ds-validate`, as a fourth structural question alongside time, groups, and
  imbalance.
- A model scores well in CV but the leaderboard/production/holdout score is
  substantially worse — the classic symptom of unaddressed shift.
- NOT for: leakage inside a feature (see `target-leakage-detection`) — shift is about
  train and test/production being drawn from different distributions, not about a
  feature encoding the target.

## Core Process

1. **Adversarial validation:** label every training row `0` and every test/production
   row `1` (using only features available in both), fit a classifier to discriminate
   them, and cross-validate its AUC.
   - AUC ≈ 0.5: train and test look like the same distribution — proceed normally.
   - AUC ≫ 0.5 (roughly >0.7): the classifier can tell train and test apart easily —
     real distribution shift exists, and CV performance is at risk of not
     transferring.
2. If shift is detected, use the adversarial classifier's own feature importance to
   find *which* features drive the separation — that tells you what changed (a
   feature whose meaning drifted, a time-dependent feature, a population change) more
   directly than eyeballing every column.
3. For each of the top drifting features, compare train vs. test distributions
   directly (histogram overlay for numeric, value-count comparison for categorical) to
   confirm the adversarial signal against something visual, not just a single AUC
   number.
4. Decide the fix based on what's driving it: drop or reweight a feature that drifted
   for a spurious reason (e.g. an ID-like column, a date artifact); if the drift is a
   genuine, expected population/time change, adjust the validation split (e.g. move to
   a temporal holdout that mimics the real gap) rather than the features.
5. Record the adversarial-validation AUC and any features flagged in
   `.last-ds-mile/stages/05-validate.md` alongside the split decision — this is
   evidence for *why* the split was chosen, not a separate report.

## Techniques/Patterns

| Situation | Technique |
|---|---|
| Kaggle-style competition with a fixed test set | Concatenate train + test, adversarial-validate before touching features; do this once, early, alongside `/ds-validate` |
| No separate test set yet (only a validation split you're choosing) | Adversarial-validate train-candidate vs. validation-candidate under each split strategy being considered — a good split should score near AUC 0.5 |
| Production monitoring after deployment | Same technique, run periodically: today's incoming data vs. the original training set — an increasing adversarial AUC over time is an early drift signal, not just a training-time check |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The CV score is stable across folds, so it'll hold on the real test set" | Fold stability proves the split is internally consistent, not that the test set resembles training. Those are independent questions — this skill answers the second one. |
| "Train and test came from the same collection process, shift isn't a concern here" | That's a hypothesis, not a check — adversarial validation costs one classifier fit and either confirms it or catches the case where "same process" quietly wasn't (a schema change, a new source, a seasonal gap). |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| Strong CV score, weak leaderboard/production/holdout score | The single clearest symptom of unaddressed distribution shift — run adversarial validation before concluding the model or the metric is at fault. |
| Adversarial-validation AUC well above 0.5 | Train and test are distinguishable — trace it to specific features before trusting any CV-based comparison between candidate models. |

See `ds-method`'s Red Flags for the shared list.

## Verification

- [ ] Adversarial validation run between train and test/production whenever a fixed
      test set or deployment population exists, not assumed to match by default.
- [ ] If shift was detected, the driving features were identified and a stated fix
      (feature-level or split-level) was applied, not just noted and left alone.
- [ ] The adversarial-validation result is recorded in `/ds-validate`'s output as part
      of the split justification.
