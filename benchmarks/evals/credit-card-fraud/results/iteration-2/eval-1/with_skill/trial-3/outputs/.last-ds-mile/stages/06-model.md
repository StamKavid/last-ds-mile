# 06 — Modeling

## Gate check

- `.last-ds-mile/stages/04-baseline.md` exists — PR-AUC anchor = 0.00167.
- `.last-ds-mile/stages/05-validate.md` exists — chronological 80/20 outer
  split, stratified 5-fold inner CV on the training 80%, reused verbatim
  (`model_train.py`).

## Experiments (5-fold stratified CV on training 80%, PR-AUC = average precision)

| Candidate | Val PR-AUC (mean ± std) | Train PR-AUC (mean) | Lift over baseline (0.00167) |
|---|---|---|---|
| Logistic Regression (`class_weight="balanced"`) | 0.704 ± 0.029 | 0.713 | 422x |
| Random Forest (300 trees, `class_weight="balanced_subsample"`) | 0.847 ± 0.028 | 1.000 | 507x |
| **XGBoost** (400 trees, depth 5, lr 0.05, `scale_pos_weight` tuned) | **0.860 ± 0.031** | 0.99999 | **515x** |
| XGBoost, regularized (depth 3, reg_alpha 1.0, reg_lambda 5.0, min_child_weight 5) | 0.835 ± 0.028 | 0.951 | 500x |
| Blend: 0.5·RF + 0.5·regularized-XGBoost | 0.855 ± 0.029 | — | 512x |

All three structurally different candidates (linear, bagging, boosting)
clear the baseline by two-plus orders of magnitude, and the gap between the
best (XGBoost, 0.860) and weakest (logreg, 0.704) tree-vs-linear candidates
(0.156) is roughly 5x the fold spread (~0.03), so the ranking is a real
effect, not fold noise.

## Winning candidate

**XGBoost**, val PR-AUC 0.860 ± 0.031 — best of all five configurations
tried, including the ensembling and regularization attempts below.

## Bias/variance diagnosis

Winning candidate shows a large train-val gap: train PR-AUC ≈ 1.000 vs.
validation 0.860 (Random Forest shows the same pattern: 1.000 vs 0.847).
This is the classic variance/overfitting signature — tree ensembles can
near-perfectly rank the ~80-100 fraud cases present in each training fold.

**Lever tried**: regularization (shallower trees, L1/L2 penalties, higher
`min_child_weight`) per the "variance → simplify" playbook. Result: gap
narrowed (train 0.951 vs val 0.835) but *validation* PR-AUC also dropped
(0.860 → 0.835) — a net loss, not a win. Read: with only ~400 fraud
examples in the training window, the model has too little positive-class
data for regularization to trade "less memorization" for "better
generalization" — it just underfits the signal instead. Not pursuing
further regularization on this budget of positive examples; flagging for
`/ds-evaluate` to confirm the CV estimate holds on the untouched
chronological test set (the real check on whether 0.860 is trustworthy
despite the training-fold gap).

**Ensembling**: tried per `model-ensembling` guidance since two structurally
different candidates (RF, XGBoost) were both trained — a 50/50 probability
blend (using the regularized XGBoost) scored 0.855, essentially tied with
but not beating the single best XGBoost (0.860). Not adopting the blend;
added complexity isn't earning its keep here.

## Frozen decision threshold

Chosen on out-of-fold predictions from the training split only (5-fold CV,
same folds as above), **before** any evaluation on the held-out test set —
maximizing F1 as an illustrative, cost-neutral choice per `/ds-frame`'s
assumption (no confirmed cost asymmetry between false positives and false
negatives):

- **Threshold = 0.681** (predicted fraud probability)
- At this threshold, out-of-fold: precision = 0.907, recall = 0.835, F1 = 0.869

This threshold is frozen and will be applied as-is to the chronological
test set in `/ds-evaluate` — it will not be re-tuned against test results.
Flagged explicitly (again) that a real deployment should replace this
F1-maximizing threshold with one chosen from the actual cost of a missed
fraud vs. a false alarm.

## Artifacts

- `model_train.py` — trains the three original candidates, 5-fold CV.
- `model_train2.py` — regularized XGBoost + blend experiments.
- `model_threshold.py` — derives the frozen threshold from OOF predictions.
- `final_model.joblib` — winning XGBoost pipeline fit on the full training
  80% (feature scaling + classifier), ready for `/ds-evaluate` to score
  against the held-out chronological test set.
- `cv_results.json`, `cv_results2.json`, `frozen_threshold.json` — raw
  numbers backing the tables above.
