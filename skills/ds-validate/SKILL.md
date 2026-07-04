---
name: ds-validate
description: Chooses a leakage-safe validation or cross-validation strategy (temporal, grouped, or stratified) that matches the data's structure, decided before any model is trained. Use before /ds-model, or when asked to set up train/test splits or cross-validation.
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
4. If none of the above apply, plain (or stratified) k-fold is fine — state that
   explicitly rather than choosing it by default without checking.
5. Write to `.last-ds-mile/stages/05-validate.md`: the chosen strategy, why, and the
   exact split/CV code to be reused identically in `/ds-model`.

## Common Rationalizations

See `ds-method` for the shared Rationalizations that apply to every stage, in particular
"I'll pick the validation strategy after I see how the data looks in modeling" — that is
exactly the rationalization this stage exists to prevent.

## Red Flags

See `ds-method`'s Red Flags — in particular, "validation metric beats the training
metric" is this stage's clearest signal of a broken or shuffled temporal split.

## Verification

- [ ] Time, group, and imbalance questions all answered explicitly, not skipped.
- [ ] Chosen strategy documented with its justification.
- [ ] Exact split/CV code recorded for identical reuse in `/ds-model`.
- [ ] `.last-ds-mile/stages/05-validate.md` written.
