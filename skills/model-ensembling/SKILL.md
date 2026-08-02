---
name: model-ensembling
description: Blends, stacks, or averages several trained models using leakage-safe out-of-fold predictions, and reports the lift over the best single component relative to fold spread. Use when someone asks to combine models, average predictions, or stack them. Use when a single model's score has plateaued and the next lever is a combination rather than a better model.
---

# model-ensembling

## Overview

Most of the score left after a good single model is trained comes from combining
models that err *differently*, not from finding one better model. This skill covers
the three practical ways to do that, and how to evaluate the result without leaking or
fooling yourself about whether the combination helped.

## When to Use

- At least two structurally different candidates exist in `/ds-model`'s experiments
  table (different model families, or the same family with meaningfully different
  feature encodings).
- A single model's score has plateaued and further tuning isn't moving it.
- NOT for: combining two near-identical models (e.g. two random seeds of the same
  config) — marginal variance reduction, not worth the added complexity.

## Core Process

1. Pick candidates likely to err *differently*, not just candidates that score well
   individually — a linear model blended with a tree model beats two similar
   boosted-tree configs with different seeds.
2. Build the blend/stack using each component's **out-of-fold predictions** on the
   *same* folds from `/ds-validate` — never predictions from a model that trained on
   the row being predicted. Same leakage rule as any other fit-requiring step: weights
   or a meta-model fit on in-sample predictions will look better than they perform.
3. Choose a combination method matched to how much data and how many components exist
   (table below) — a weighted average needs almost no data; a stacking meta-model
   needs enough OOF rows to avoid overfitting to the blend itself.
4. Compare the ensemble's OOF score to its **best single component's** OOF score, same
   folds, same spread reporting (see `uncertainty-quantification`) — the lift must
   exceed fold-to-fold noise, not just move the mean.
5. If the ensemble wins, it's the candidate carried into `/ds-evaluate`; if it doesn't
   clear the noise bar, ship the best single component instead and say so.

## Techniques/Patterns

| Method | When to use | Leakage risk |
|---|---|---|
| Simple average / weighted average | 2-4 components, little data to spare for fitting weights, or as the first thing to try | Low — weights can even be picked by eye from OOF scores; if grid-searching weights, search them against OOF predictions only, never against training-fold predictions |
| Rank averaging | Components produce scores on very different scales (e.g. mixing a probability with a raw score) | Same as weighted average |
| Stacking (meta-model trained on OOF predictions as features) | 3+ components, enough rows that a simple meta-model (e.g. `Ridge`) won't overfit to the blend itself | Higher — the meta-model must be fit on OOF predictions only, and its own performance must be estimated via a further CV loop over those OOF predictions, not evaluated on the same rows used to fit it |
| Seed averaging (same model, several random seeds, averaged) | A single model type with genuinely high seed-to-seed variance (high fold std even for a fixed config) | Low, but yields the smallest lift of the four — it reduces variance, not bias, so it doesn't help a model that's just wrong, only one that's noisy |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "More models in the blend is always better" | Diminishing, sometimes negative returns once components are similar — diversity of errors matters more than count. |
| "The blend's mean score is higher, so it worked" | Check it against the noise (`uncertainty-quantification`). A "win" smaller than the fold std costs 2-3x inference complexity for no demonstrated gain. |
| "I'll fit the stacking meta-model on the full training predictions, it's just a simple Ridge" | In-sample base-model predictions are artificially close to the truth, so the meta-model learns a distorted, over-optimistic weighting. OOF only. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| An ensemble's OOF score improves by less than any component's fold std | Not a demonstrated improvement — see `uncertainty-quantification`. Ship the best single component instead. |
| A stacking meta-model was fit on training-fold (not out-of-fold) base predictions | Leakage into the ensemble weights — the blend's reported score will not reproduce at inference time on genuinely new rows. |
| Every component in the blend is the same model family with only the random seed changed | Seed-averaging masquerading as ensembling — real, but the smallest possible lift of the four techniques above; don't expect it to fix a biased model. |

See `ds-method`'s Red Flags for the shared list.

## Verification

- [ ] Every ensemble component's contribution is built from out-of-fold predictions,
      never in-sample predictions.
- [ ] The ensemble's score is compared to its best single component's score on the
      same folds, with both reported as mean ± std.
- [ ] The lift (if any) is stated relative to that spread, not as a bare "higher
      mean."
- [ ] If the ensemble didn't clear the noise bar, the best single component ships
      instead, and that decision is recorded, not silently defaulted to the more
      complex option.
