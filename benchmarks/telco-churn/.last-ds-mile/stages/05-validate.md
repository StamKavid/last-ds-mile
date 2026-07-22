# Stage 5 — Validation Design

## Time question

**No time dimension exists in this dataset** — it's a single snapshot, not
time-ordered transactions or sales (no date/timestamp column at all). Checked
explicitly, not skipped: there is no `YrSold`-equivalent to split on, and no temporal
holdout is possible or meaningful here. Stated rather than silently omitted, per
`ds-validate`'s requirement to answer the question even when the answer is "doesn't
apply."

## Group question

No repeated entity — `customerID` is confirmed unique (0 duplicates), one row per
customer. No `GroupKFold` need.

## Imbalance question

**Moderate**: 26.5% churn. Real enough to require `StratifiedKFold` (a plain shuffled
k-fold risks meaningfully different churn rates across folds at this scale — 7043
rows / 5 folds ≈ 1409 rows per fold, where sampling noise on a 26.5% rate is not
negligible), but not severe enough to make ROC-AUC itself misleading the way
credit-card-fraud's 0.17% does (see `/ds-frame`'s metric choice).

## Chosen strategy — reused identically in `/ds-model`

```python
from sklearn.model_selection import StratifiedKFold

def build_cv_splitter(y, n_splits=5, seed=42):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(skf.split(np.zeros(len(y)), y))
```

**Verified structurally:** 5 stratified folds of ~1409 rows each, preserving the
26.5% churn rate per fold.
