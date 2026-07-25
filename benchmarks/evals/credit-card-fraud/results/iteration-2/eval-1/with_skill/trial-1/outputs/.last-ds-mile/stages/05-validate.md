# 05 — Validation Design

Implementation: `validate_check.py`. Decided before any candidate model is
trained, on the deduplicated dataset from `/ds-prep` (283,726 rows).

## Time dimension — could future data leak into past predictions?
`Time` spans a single 2-day window and only the derived `hour` feature is
used (raw `Time` was dropped in `/ds-prep`). Checked whether the two classes'
relationship is stable across the window rather than assuming it: split at
the median `Time` and compared the first vs. second half.

| | First half | Second half |
|---|---|---|
| n | 141,863 | 141,863 |
| Fraud count | 262 | 211 |
| Fraud rate | 0.185% | 0.149% |
| PR-AUC of `-V14` alone | 0.6046 | 0.6279 |
| V14 mean, fraud rows | -7.19 | -6.40 |
| V14 mean, genuine rows | 0.04 | -0.02 |

Fraud rate, single-feature PR-AUC, and class-conditional feature means are
all close across the two halves — **no meaningful distribution shift within
this capture window**. A strict chronological split isn't needed to protect
against within-window drift; a stratified split is safe here. (Caveat for
`/ds-report`: this only checks stability *within* the 2-day capture window,
not whether fraud patterns from Sept 2013 generalize to today — that's a
production-monitoring concern outside this dataset's scope, not something
a validation split choice can fix.)

## Group structure — same entity across multiple rows?
No card/customer/merchant ID exists in this anonymized dataset, so there's
no key to group-split on. The specific risk this would normally guard
against — the same physical transaction appearing in both train and test —
was already addressed in `/ds-prep` by dropping the 1,081 exact-duplicate
rows before any split. No further grouping action available or needed.

## Imbalance
Severe: 0.167% fraud (473 of 283,726 rows). A plain random split risks
folds with very few or zero fraud examples. **Stratified splitting is
required**, not optional here.

## Fixed test set / deployment population
No separate held-out test set is provided (single CSV) and no production
population to adversarially validate against yet — noted as an open item
for `/ds-handoff` (a live deployment should re-run a distribution-shift
check against production traffic before trusting these numbers).

## Chosen strategy
1. **Final holdout**: one stratified 80/20 train/test split
   (`train_test_split(..., stratify=y, random_state=42)`). Train: 226,980
   rows / 378 fraud (0.167%). Test: 56,746 rows / 95 fraud (0.167%) — held
   out untouched until `/ds-evaluate`, used exactly once for final reporting.
2. **Model selection / tuning**: 5-fold `StratifiedKFold(shuffle=True,
   random_state=42)` within the training partition only. Fraud count per
   validation fold: [75, 75, 76, 76, 76] — enough fraud examples per fold to
   get a stable PR-AUC estimate.
3. Both the holdout split and the CV folds are stratified on `Class`, use
   `random_state=42` for reproducibility, and are computed on the
   already-deduplicated dataset from `/ds-prep`. `/ds-model` reuses this
   exact split — it is not re-derived or tuned per model.
