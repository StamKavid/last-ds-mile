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
3. Track each experiment's configuration and score, reported as mean ± standard
   deviation across folds (see `uncertainty-quantification`), not a single collapsed
   number. A plain markdown table is sufficient at this scale; a full
   experiment-tracking tool is optional, not required.
4. Compare every candidate explicitly to the baseline score from `/ds-baseline`. State
   the lift (or lack of it) plainly, in the same units as the metric, and state whether
   that lift exceeds the fold spread — a lift smaller than the noise is not a
   demonstrated improvement (see `uncertainty-quantification`).
5. **Bias/variance diagnosis for the winning candidate:** compute its training-fold
   score alongside its validation-fold score (both already produced by step 2's CV
   loop — this is not an extra training run). A large gap (validation much worse than
   training) means variance/overfitting — more data, regularization, or a simpler
   model is the next lever. A small gap where both scores are still far from the
   baseline-beating target means bias — a richer feature set (`/ds-prep`) or a more
   expressive model class is the next lever, not more regularization. State which
   diagnosis applies; don't skip straight to "let's try another model" without it.
6. Once at least two structurally different candidates are trained, consider whether
   combining them (a blend, a stack, or averaging) beats the best single one — see
   `model-ensembling`. Not required for every run, but don't stop at the first
   plateaued single model without at least checking.
7. **If the deployment decision requires a hard threshold** (classification only —
   e.g. flag as fraud above probability X, not just rank-order risk): choose the
   threshold using validation-fold predictions only, using the cost asymmetry from
   `/ds-frame`/`metric-selection` (not 0.5 by default), and freeze it before any
   evaluation on held-out data. Record the frozen threshold and how it was chosen —
   tuning it later against evaluation results is the same leakage pattern as peeking
   at a test set.
8. Write to `.last-ds-mile/stages/06-model.md`: the experiments table (with spread),
   the best candidate, its lift over baseline relative to that spread, the
   bias/variance diagnosis, any ensembling result, and the frozen threshold if one
   applies.

## Common Rationalizations

See `ds-method` for the shared Rationalizations that apply to every stage, in particular
"I'll just peek at the test set once" — the temptation is strongest exactly at this
stage, during tuning.

## Red Flags

See `ds-method`'s Red Flags, in particular "metric looks too good on the first try" —
the single most common signal that something upstream (usually in `/ds-prep`) leaked.

| Red Flag | What it usually means |
|---|---|
| One candidate scores dramatically worse than several structurally similar candidates trained on the identical split | A bug in that candidate's specific configuration (e.g. a library-specific imbalance-weighting parameter breaking at an extreme ratio), not evidence that "this model just doesn't fit the data" — diagnose on a quick held split before trusting or discarding the number. |

See `lessons/the-imbalance-knob-that-broke-silently.md` for a real example.

## Verification

- [ ] Gate check passed: both `.last-ds-mile/stages/04-baseline.md` and
      `.last-ds-mile/stages/05-validate.md` exist and were read before modeling began.
- [ ] The same validation code from `/ds-validate` was reused, not rewritten.
- [ ] Every candidate model's score includes its fold spread, not a bare mean.
- [ ] Every candidate model is compared to the baseline score explicitly, stating
      whether the lift exceeds the fold spread.
- [ ] The winning candidate's train-vs-validation gap was checked and diagnosed as
      bias or variance, not skipped.
- [ ] If a hard decision threshold is needed, it was chosen on validation predictions
      only and frozen before any held-out evaluation.
- [ ] `.last-ds-mile/stages/06-model.md` written.
