# 03 — Cleaning & Feature Engineering

## Cleaning log

| Change | Why | Alternative considered |
|---|---|---|
| Drop exact duplicate rows, keep first occurrence (284,807 → 283,726 rows; fraud 492 → 473) | Duplicates flagged in `01-data.md` as a validation-split leakage risk — an identical row appearing in both train and test would let the model "memorize" it. Deduplicating before splitting removes that risk at the source. | Keep duplicates but ensure split is duplicate-aware (group-based split on a hash of the row). Rejected as unnecessary complexity here since dropping loses only 0.4% of rows and no known business meaning of "repeated identical transaction" was confirmed. |
| No missing-value imputation | Zero missing values across all columns (`01-data.md`). | N/A |
| No outlier removal on `Amount` or `V*` | Fraud is disproportionately likely to look "extreme" — removing outliers would risk deleting real fraud cases, not noise. | Winsorizing considered and rejected for the same reason. |

## Feature list (known-at-prediction-time justification)

| Feature | Included? | Justification |
|---|---|---|
| `V1`–`V28` | Yes, as-is | PCA of transaction attributes available at authorization time; not derived from `Class` or any post-transaction outcome. |
| `Amount` | Yes, as-is + `Amount_log = log1p(Amount)` added | Transaction amount is known at authorization time. Added a log1p transform alongside the raw value because `Amount` is heavily right-skewed (`02-explore.md`); both are known-at-prediction-time, kept together and let the model/regularization decide which is useful — not a leakage concern either way. |
| `Time` | Yes, as-is | Seconds since dataset start is a proxy for intra-window recency, known at prediction time. Explicitly noted: with only a 48-hour window and no wall-clock semantics, this feature's learned association may not generalize beyond this dataset's specific window — a modeling/generalization caveat, not a leakage one. Kept because dropping it a priori without evidence it's harmful would throw away signal; its usefulness is re-checked via feature importance in `/ds-evaluate`. |
| `Class` | N/A | Target, not a feature. |

No feature required target-derived aggregates, rolling windows, or any
computation spanning the train/test boundary, so the "time-traveling
feature" red flag does not apply here.

## Leakage candidates resolved

- Duplicate rows (flagged in `01-data.md`): resolved by dedup above, and
  will be re-confirmed as a non-issue in `/ds-validate` by checking the
  split has no shared rows (should be moot post-dedup, but verified anyway
  since dedup only catches *exact* duplicates, not near-duplicates from
  future data).
- No feature-level leakage candidates were flagged in `/ds-explore` (see
  `02-explore.md`) — `V14`/other strong separators are pre-label PCA
  features, not disguised target copies.

## Pipeline definition

All fit-requiring transforms are wrapped in a single `sklearn.Pipeline` so
scaling is fit on training folds only, never on the full dataset:

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer

numeric_features = [f"V{i}" for i in range(1, 29)] + ["Time", "Amount", "Amount_log"]

preprocess = ColumnTransformer([
    ("scale", StandardScaler(), numeric_features),
])

pipeline = Pipeline([
    ("preprocess", preprocess),
    ("clf", None),  # estimator plugged in at /ds-model
])
```

`Amount_log` is computed once as a deterministic row-wise transform
(`log1p`, no fitting required) before the pipeline, so it's safe to compute
on the full dataset prior to splitting — unlike `StandardScaler`, it uses no
cross-row statistics.
