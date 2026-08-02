# 06 — Modeling

## Candidates tried (identical temporal split/features from `05-validate.md` / `03-prep.md`)

| Model | PR-AUC | ROC-AUC |
|---|---|---|
| Baseline (no-skill) | 0.0013 | 0.500 |
| Logistic Regression (`class_weight="balanced"`) | 0.769 | 0.980 |
| **Random Forest** (`class_weight="balanced"`, 300 trees) | **0.814** | 0.959 |
| HistGradientBoosting (default) | 0.428 | 0.852 |

All three clear the baseline by a wide margin. **Random Forest selected** as best on
the primary metric (PR-AUC). HistGradientBoosting underperforms here without any
imbalance-specific tuning (no class weighting applied) — included as a stock
comparison, not further tuned, since Random Forest already had a clear edge and
tuning every candidate wasn't warranted.

## Stability check
5-fold stratified CV of the Random Forest *within the training period only* (never
touching the test set): PR-AUC = 0.851 ± 0.035 across folds (range 0.811–0.894,
~73 fraud cases per validation fold). This is consistent with the 0.814 seen on the
temporal holdout — the holdout score is not an outlier, and the gap is explained by
the fraud-rate drop in the later period noted in `05-validate.md`, not by leakage or
overfitting.

## Feature importance (Random Forest)
Top drivers: `V14` (0.157), `V10` (0.122), `V4` (0.107), `V12` (0.107), `V17` (0.082),
`V11` (0.068) — consistent with the correlation screen in `02-explore.md`, which also
flagged `V14`, `V17`, `V12`, `V10` as the strongest linearly-separating features. No
surprise "one feature does everything" pattern that would suggest a leaked proxy for
the target.

## Hyperparameters
Used reasonable defaults (`n_estimators=300`, `class_weight="balanced"`, no other
tuning) rather than an extensive search — justified because the gap over the
baseline and over the other candidates is already large (PR-AUC 0.81 vs 0.001
baseline), so marginal tuning gains weren't the priority for this pass. Documented
here so it's flagged as unfinished tuning if this line is revisited later.
