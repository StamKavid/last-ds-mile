# 03 — Cleaning & Feature Engineering

Implementation: `fraud_pipeline.py` (`load_clean_data`, `build_preprocessor`,
`build_pipeline`) — shared by `/ds-baseline`, `/ds-validate`, and `/ds-model`
so every stage trains/evaluates on identically prepared data.

## Cleaning log

| Change | Why | Alternative considered |
|---|---|---|
| Drop 1,081 exact full-row duplicates (473 fraud rows remain, down from 492; 283,726 rows remain, down from 284,807) | Duplicates are exact-value collisions across all 30 raw columns — per `/ds-explore`, they're disproportionately fraud (1.7% vs 0.16%) and, left in, would let identical rows land in both train and test, letting the model "recognize" a memorized row instead of generalizing. This is a data-integrity fix applied to the whole dataset before any split, not a statistic computed over train+test, so it carries no leakage risk itself. | Keep duplicates and de-risk only via grouped train/test split. Rejected: simpler and more conservative to just drop them once, and matches known treatment of this public dataset in the literature. |

No missing values to impute (confirmed in `/ds-data`). No categorical
encoding needed (all columns numeric).

## Feature list — known-at-prediction-time justification

| Feature | Known at prediction time? | Justification |
|---|---|---|
| `V1`–`V28` (28 features) | Yes | Per-transaction PCA components computed by the dataset publisher from attributes available at the transaction itself; no post-outcome fields exist in this dataset (confirmed in `/ds-frame`'s information inventory). |
| `log_amount` = `log1p(Amount)` | Yes | Deterministic transform of `Amount`, which is known the instant a transaction is initiated. Used in place of raw `Amount` to reduce the right-skew noted in `/ds-explore` (helps linear models; harmless for tree models). |
| `hour` = `(Time // 3600) % 24` | Yes | Time-of-day is known at the instant of the transaction. Derived from `Time`, which itself is dropped from the model (see below). |

**Dropped**: raw `Time` and raw `Amount` are not used directly as model
features — `Time` is an offset into this specific 2-day capture window and
wouldn't generalize to a model scoring transactions on a different date;
`hour` extracts the generalizable cyclical signal from it instead. `Amount`
is superseded by `log_amount`.

## Leakage candidates from `/ds-explore` — resolution

1. **V14/V4/V12 high single-feature AUC**: resolved as genuine signal in
   `/ds-explore` (no post-outcome field exists that could have leaked into
   PCA components computed by the publisher). No action needed here.
2. **Duplicate rows correlating with fraud**: resolved above — deduplicated
   before any split.
3. **`Time` encoding row order**: resolved by dropping raw `Time` from the
   feature set (only the cyclical `hour` derivative is used) and deferring
   the split-order question to `/ds-validate`.

## Pipeline definition

All fit-requiring transforms (`StandardScaler` over the 30 feature columns)
are wrapped in a `ColumnTransformer` inside an `sklearn.Pipeline`
(`build_pipeline(estimator)` in `fraud_pipeline.py`). The scaler is never
fit on the full dataset — it's fit inside each train fold only, via the
pipeline's `.fit()` during cross-validation / train-test fitting in
`/ds-baseline`, `/ds-validate`, and `/ds-model`.
