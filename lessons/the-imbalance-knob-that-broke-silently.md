---
title: The Imbalance Knob That Broke Silently
skills: [imbalanced-data, ds-model]
stages: []
---

# The Imbalance Knob That Broke Silently

A fraud-detection benchmark trained five gradient-boosting and linear candidates
against a severely imbalanced target (0.17% positive, roughly 600:1). Four scored
PR-AUC 0.72–0.84. The fifth — LightGBM, configured with the textbook
`scale_pos_weight = (1-rate)/rate` fix for imbalance — scored **0.04**, with a wild,
unstable fold-to-fold spread. It wasn't quietly worse. It had collapsed.

The instinct to explain this away was right there: "LightGBM just doesn't handle
this dataset as well," or worse, just dropping it from the comparison table as an
underperformer and moving on with the other four. Neither is what happened. A model
scoring 20x worse than five structurally similar candidates on the same data, same
split, same target is a bug signal, not a modeling-choice footnote — the whole point
of running candidates side by side is that an outlier this extreme should stop you,
not get silently averaged away.

A quick, isolated diagnostic on a single held split found the cause: swapping
*only* `scale_pos_weight=599` for `class_weight="balanced"` — same model, same data,
same split — took PR-AUC from 0.017 to 0.887. `is_unbalance=True` showed the
identical collapse; changing `min_child_samples` barely moved it. XGBoost and
CatBoost's own imbalance-weighting equivalents, run at the same ~600:1 ratio, never
showed the problem. The mechanism, not just the value, mattered: `scale_pos_weight`
scales LightGBM's boosting gradient directly, and at extreme ratios that path hits a
numerical-stability wall that per-sample class reweighting doesn't.

**Lesson:** a candidate that scores dramatically worse than several structurally
similar candidates trained on the identical split is evidence of a bug, not evidence
that "this model just doesn't fit this data" — check before you believe either
story. And a library's most commonly recommended imbalance parameter is not
guaranteed to be numerically stable at every imbalance ratio; if scale_pos_weight (or
any similar single-scalar reweighting knob) produces a degenerate score under severe
imbalance, try the library's alternative weighting mechanism (here, class_weight)
before concluding the model itself is the wrong choice.
