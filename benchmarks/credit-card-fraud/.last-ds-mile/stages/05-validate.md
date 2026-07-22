# Stage 5 — Validation Design

## Time question

**Yes, a real time dimension exists** (`Time`, seconds elapsed over ~2 days), and
`/ds-explore` found a mild fraud-rate drift (0.194% day 0 vs. 0.151% day 1) plus a
strong hour-of-day pattern. Unlike house-prices' multi-year deployment horizon, this
dataset's 2-day span is too short for a temporal holdout to be the *primary*
evaluation scheme — a single day-1-only holdout would be a small, noisy sample of
only ~140K rows with ~220 fraud cases, and a real fraud-screening deployment retrains
far more frequently than "once, on all past data" anyway. **Decision**, same
two-mechanism pattern as house-prices:
1. **Primary tuning/comparison:** stratified 5-fold CV (below), used throughout
   `/ds-model`.
2. **Secondary, one-time temporal robustness check:** train on `day == 0`, evaluate
   once on `day == 1` — not used for tuning, a final sanity check only.

## Group question

No repeated entity is identifiable — this dataset has no customer/card ID (removed
during the source publisher's anonymization), so there's no key to group by. No
`GroupKFold` need here, stated explicitly rather than skipped.

## Imbalance question

**Severe**: 0.167% fraud (473/283,726) after deduplication. `StratifiedKFold` is not
optional here the way it might be at milder imbalance — a plain shuffled k-fold risks
a fold with a handful or zero fraud cases, making PR-AUC on that fold meaningless.

## Chosen strategy — reused identically in `/ds-model`

```python
from sklearn.model_selection import StratifiedKFold

def build_cv_splitter(y, n_splits=5, seed=42):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(skf.split(np.zeros(len(y)), y))

def temporal_holdout_mask(df):
    return df["day"] == 0, df["day"] == 1
```

**Verified structurally:** 5 stratified folds preserve the 0.167% fraud rate in both
train and validation portions of every fold (checked directly via
`y[va_idx].mean()` per fold, not assumed from the splitter's contract alone).
Deduplication (see `/ds-prep`) happens *before* this split, so no duplicate
transaction can land in both a training and validation fold.
