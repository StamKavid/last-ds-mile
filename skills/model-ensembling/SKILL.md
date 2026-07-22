---
name: model-ensembling
description: Blends, stacks, or averages multiple trained candidates using leakage-safe out-of-fold predictions, and reports the ensemble's lift over its own best single component relative to the fold spread. Use during /ds-model once at least two structurally different candidates have been trained, or when a single model's score has plateaued and the next lever isn't a better model but a combination of the ones already trained.
---

# model-ensembling

## Overview

Most of the score left on the table after a good single model is trained comes from
combining models that make *different* mistakes, not from finding one better model.
This skill covers the three practical ways to do that, and — the part that actually
matters — how to evaluate the result without leaking or fooling yourself about
whether the combination helped.

## When to Use

- At least two structurally different candidates already exist in `/ds-model`'s
  experiments table (different model families, or the same family with meaningfully
  different feature encodings — e.g. one-hot vs. a model's native categorical
  handling).
- A single model's score has plateaued and further hyperparameter tuning isn't
  moving it — combining models is a different lever than tuning one further.
- NOT for: combining two near-identical models (e.g. two random seeds of the same
  LightGBM config) — that reduces variance marginally at best and isn't worth the
  added complexity; see the Common Rationalizations table.

## Core Process

1. Pick candidates that are likely to err *differently*, not just candidates that
   score well individually — a linear model blended with a tree model, or the same
   boosting algorithm run with genuinely different feature encodings (one-hot vs.
   native categorical handling), is a better blend candidate than two similar
   boosted-tree configs with different seeds.
2. Build the blend/stack using each component's **out-of-fold predictions** on the
   *same* folds from `/ds-validate` — never predictions from a model that trained on
   the row being predicted. This is the same leakage rule as any other fit-requiring
   step: an ensemble weight or a stacking meta-model fit on in-sample predictions will
   look better than it will actually perform.
3. Choose a combination method matched to how much data and how many components exist
   (see the table below) — a weighted average needs almost no data to fit safely; a
   stacking meta-model needs enough OOF rows to fit reliably without overfitting to
   the blend itself.
4. Compare the ensemble's OOF score to its **best single component's** OOF score, on
   the same folds, with the same spread reporting as everything else (see
   `uncertainty-quantification`) — report whether the lift exceeds the components'
   own fold-to-fold noise, not just whether the mean moved.
5. If the ensemble wins, it becomes the candidate carried into `/ds-evaluate`; if it
   doesn't clear the noise bar, ship the best single component instead and say so —
   an ensemble that doesn't demonstrably help is unneeded complexity for handoff.

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
| "More models in the blend is always better" | Diminishing, sometimes negative returns once components are similar — a 5-model blend of near-identical boosted trees can underperform a 2-model blend of a tree model and a linear model. Diversity of errors matters more than count. |
| "The blend's mean score is higher, so it worked" | Check it against the noise, same as any other model comparison — see `uncertainty-quantification`. A blend that "wins" by less than the fold std hasn't demonstrated anything, and now costs 2-3x the inference complexity for that non-improvement. |
| "I'll fit the stacking meta-model on the full training predictions, it's just a simple Ridge" | A meta-model fit on in-sample (non-OOF) base-model predictions sees each base model's predictions for rows it was trained on — those predictions are artificially close to the truth, so the meta-model learns a distorted, over-optimistic weighting. Same rule as any other fit-requiring transform: OOF only. |

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
