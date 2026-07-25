# 06 — Modeling

## Gate check
`.last-ds-mile/stages/04-baseline.md` (PR-AUC anchor 0.605) and
`.last-ds-mile/stages/05-validate.md` (stratified 80/20 holdout + 5-fold
`StratifiedKFold` on the training partition, `random_state=42`) both exist
and were reused exactly — same split indices, same fold assignment,
implemented once in `fraud_pipeline.py`/`model.py`.

## Experiments (5-fold CV on the training partition, PR-AUC)

| Candidate | Val PR-AUC (mean ± std) | Fold scores | Train PR-AUC |
|---|---|---|---|
| Logistic regression (`class_weight="balanced"`) | 0.7406 ± 0.0226 | 0.750, 0.738, 0.698, 0.757, 0.761 | 0.7442 |
| XGBoost (`max_depth=4, n_estimators=300, lr=0.1, scale_pos_weight`) | **0.8441 ± 0.0275** | 0.847, 0.859, 0.790, 0.867, 0.857 | 1.0000 |
| Ensemble (avg of OOF probabilities, LR + XGBoost) | 0.8491 | — (derived) | — |
| XGBoost, regularized (`max_depth=3, subsample=0.8, colsample=0.8, reg_lambda=5, min_child_weight=5`) | 0.8040 ± 0.0340 | 0.824, 0.828, 0.737, 0.811, 0.821 | 0.9224 |

## Comparison to baseline (0.605 PR-AUC, `-V14` single feature)
Both real candidates clear the baseline by a wide margin relative to their
own fold spread:
- Logistic regression: **+0.136** over baseline (0.741 vs 0.605), spread
  ±0.023 — lift is ~6x the fold std, a real improvement.
- XGBoost: **+0.239** over baseline (0.844 vs 0.605), spread ±0.028 — lift
  is ~9x the fold std, a real improvement, and clearly ahead of logistic
  regression too (+0.104 over LR, also beyond either model's fold spread).

## Ensembling check
Averaging LR and XGBoost's out-of-fold probabilities gives PR-AUC 0.8491,
only **+0.0050** over XGBoost alone — smaller than XGBoost's own fold std
(0.0275). Per the lift-vs-noise rule, this is **not a demonstrated
improvement**; adding ensembling complexity isn't justified. **XGBoost alone
is the selected model.**

## Bias/variance diagnosis (winning candidate: XGBoost)
Train PR-AUC (1.000) vs. validation PR-AUC (0.844) is a large gap — a
textbook **variance/overfitting** signature: the model is expressive enough
to fit training folds almost perfectly. Next lever tried: regularization
(shallower trees, subsampling, L2, higher min-child-weight) — this *did*
narrow the train/val gap (0.922 vs 0.804, gap 0.118 vs the original 0.156),
but it also **lowered** the validation PR-AUC itself (0.804 vs 0.844,
outside the fold spread of the un-regularized model). Since validation
PR-AUC is already an honest out-of-fold estimate regardless of the training
gap, trading it away for a smaller gap isn't worth it here — **kept the
original (unregularized) XGBoost** as the selected model, but flagged this
explicitly for `/ds-evaluate`: if the held-out test PR-AUC comes in well
below 0.844, that would indicate the CV estimate itself was optimistic
(e.g. from subtle leakage) rather than a bias/variance issue, and should
route back to `/ds-validate` or `/ds-prep` per `/ds-iterate`.

## Frozen decision threshold
Chosen from **out-of-fold predictions on the training partition only**
(never touched the held-out test set), using XGBoost's OOF probabilities,
per the recall/precision tradeoff framing from `/ds-frame`:

| Precision target | Frozen threshold | Recall at that threshold |
|---|---|---|
| ≥ 0.50 | 0.0381 | 85.4% |
| ≥ 0.70 | 0.1083 | 83.9% |
| ≥ 0.90 | 0.6746 | 81.7% |

Compare to Baseline B (single-feature `-V14`) at the same precision targets:
recall was 74.2% / 55.8% / 10.6% respectively — XGBoost improves recall at
every precision band, most dramatically at the high-precision end (81.7% vs
10.6% at precision≥0.90). These thresholds are frozen for `/ds-evaluate` —
not to be re-tuned after seeing test-set results.
