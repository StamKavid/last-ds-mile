# Stage 3 — Cleaning & Feature Engineering

All code lives in `scripts/pipeline_lib.py`, imported identically by every later
stage — this stage does not hand off a description of a pipeline, it hands off the
actual pipeline.

## Cleaning log

| Decision | What | Why | Alternative considered |
|---|---|---|---|
| `NA` → `"None"` for 15 columns (`PoolQC`, `MiscFeature`, `Alley`, `Fence`, `MasVnrType`, `FireplaceQu`, 4×Garage, 5×Bsmt) | Explicit category, not imputation | Per `data_description.txt`, `NA` here means "feature absent" (no pool, no garage), not "value unknown" — imputing a fake quality rating for a nonexistent pool would be wrong | Dropping the columns entirely — rejected, "has no pool" is itself informative |
| `LotFrontage` (259 missing, train) | Imputed by **neighborhood median**, fallback to global median | A genuinely unknown continuous value; neighborhood is a reasonable proxy since lot frontage correlates with local platting patterns, and `Neighborhood` is known at listing time for every row (not a future-looking aggregate) | Global median only — rejected as less accurate; kept as fallback for `test.csv` rows whose neighborhood/subset has no train coverage |
| `GarageYrBlt` (81 missing, train) | Filled with `0` | These are exactly the "no garage" rows (same 81-row set as the other Garage-quality nulls) — `0` is an unambiguous sentinel once `HasGarage` is also present | Median-year imputation — rejected, would fabricate a fake garage age for houses with no garage |
| `MasVnrArea` (8 missing, train) | Filled with `0` | Paired with `MasVnrType="None"` for these same rows in every case checked — no veneer, so area is genuinely 0, not unknown | — |
| `Electrical` (1 missing, train) | Filled with the mode (`SBrkr`) | A single row; mode is the least-assumption fallback for one row out of 1460 | Dropping the row — rejected, unnecessary data loss for a non-target column |
| `test.csv`-only nulls (16 columns, 1–4 rows each — `MSZoning`, `Utilities`, `Exterior1st/2nd`, `KitchenQual`, `Functional`, `SaleType`, several Bsmt/Garage numerics) | Left to the `ColumnTransformer`'s `SimpleImputer` (median/most-frequent, **fit on train only**) | These are a known quirk of this Kaggle test set — a handful of rows have gaps that don't exist anywhere in train. Since the imputer's fit statistics come from train, applying them to test at inference time is leakage-safe by construction | Hand-filling these too — redundant once the pipeline already handles it correctly |

## Feature engineering

| Feature | Formula | Known-at-prediction-time justification |
|---|---|---|
| `TotalSF` | `TotalBsmtSF + 1stFlrSF + 2ndFlrSF` | Sum of three columns already recorded at listing; no future information |
| `HouseAge` | `YrSold - YearBuilt` | Both inputs recorded before/at listing |
| `RemodAge` | `YrSold - YearRemodAdd` | Same |
| `TotalBath` | `FullBath + 0.5·HalfBath + BsmtFullBath + 0.5·BsmtHalfBath` | Standard bath-count aggregation, all inputs row-local |
| `HasPool`, `HasGarage`, `HasFireplace` | `(Area/Count > 0)` | Derived from existing row-local columns |

**Explicitly not done:** no feature is computed as an aggregate over the full
dataset (e.g. "average price in this neighborhood") — that would be the
full-dataset-aggregate leakage pattern `target-leakage-detection` warns about, and it
would also leak `SalePrice` itself into a feature. `Neighborhood` is passed through as
a plain categorical instead, letting the model learn location effects without
hand-computing a target-derived statistic.

## Leakage resolution

`/ds-explore` flagged no leakage candidates. Re-checked here per this stage's own
process: every engineered feature is a same-row, pre-sale-known quantity; no
full-dataset or cross-row aggregate exists in the feature set; `SalePrice` itself is
excluded from the feature list (`get_feature_lists` explicitly drops `SalePrice` and
`logSalePrice`).

## Pipeline definition

`ColumnTransformer` (median imputation + passthrough for 43 numeric columns,
most-frequent imputation + one-hot encoding for 43 categorical columns), defined in
`build_preprocessor()`. It is **not** fit here — per `/ds-prep`'s rule, it's fit inside
each CV fold's training data only, first invoked in `/ds-validate`'s split-verification
step and reused identically through `/ds-model`.
