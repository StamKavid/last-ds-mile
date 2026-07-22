# Stage 1 — Data Understanding

## Sanitization gate

Both `train.csv` and `test.csv` are the standard Kaggle "House Prices" competition
files — public, non-sensitive tabular data, no user PII, no pickle/joblib files
involved. Scanned for hidden unicode / injected instructions in the two free-text-ish
columns (`MiscFeature`, `SaleCondition` string values) — none found. No elevated-trust
action required for this dataset.

## Shape and types

- `train.csv`: 1460 rows × 81 columns (80 features + `SalePrice`).
- `test.csv`: 1459 rows × 80 columns (identical feature set, `SalePrice` withheld —
  this is the Kaggle submission target, used here as a genuine held-out set with
  labels revealed only through the leaderboard/actuals process, not through this
  pipeline).
- Column types: 38 numeric (35 `int64`, 3 `float64`), 43 categorical (`object`).
- `Id` is a unique row identifier, 0 duplicates in either file — confirmed via
  `train['Id'].duplicated().sum() == 0`.

## Missingness

| Column | Missing (train) | Meaning per `data_description.txt` |
|---|---|---|
| PoolQC | 1453 (99.5%) | `NA` = no pool, not missing data |
| MiscFeature | 1406 (96.3%) | `NA` = none |
| Alley | 1369 (93.8%) | `NA` = no alley access |
| Fence | 1179 (80.8%) | `NA` = no fence |
| MasVnrType | 872 (59.7%) | `NA` = no masonry veneer |
| FireplaceQu | 690 (47.3%) | `NA` = no fireplace |
| LotFrontage | 259 (17.7%) | **Genuinely unknown**, not a "none" category — a continuous measurement that wasn't recorded |
| GarageType/Yr/Finish/Qual/Cond | 81 (5.5%) each | `NA` = no garage (all 5 columns null together — confirmed same 81 row set) |
| BsmtExposure/FinType2/Qual/Cond/FinType1 | 37–38 (2.5–2.6%) | `NA` = no basement, with one row (`BsmtExposure`) having a basement recorded elsewhere but this field null — a genuine partial-record gap, not "no basement" |
| MasVnrArea | 8 (0.5%) | Paired with the 872 `MasVnrType` nulls at a much lower count — these 8 need a real imputation decision, not a "none" fill |
| Electrical | 1 (0.07%) | Single row (`Id` 1380), genuinely missing — every other house has a recorded electrical system |

**Key finding:** the overwhelming majority of "missingness" here is `pandas`
misreading the dataset's own encoding — `NA` in the source data dictionary means "this
feature doesn't apply to this house" (no pool, no alley, no garage), not "unknown."
Only `LotFrontage`, `MasVnrArea`, and `Electrical` are true missing-data problems.
This distinction matters for `/ds-prep`: treating "no garage" as a missing value to
impute would be wrong — it should become an explicit `"None"` category.

## Integrity checks

- `YearBuilt > YrSold` (a house sold before it was built): **0 rows** — no impossible
  dates.
- `YearRemodAdd < YearBuilt`: checked, no violations found.
- `OverallQual`/`OverallCond` both range 1–10 as documented, no out-of-range values.
- `GarageYrBlt` max is 2010 (matches `YrSold` max), not some absurd future year —
  sanity-checked as one of the more error-prone fields in this dataset in public
  writeups (a known "GarageYrBlt=2207" typo exists in some mirrors of this dataset;
  **not present in this copy**).
- No column names or values resembling secrets/credentials.
- `Neighborhood`: 25 distinct values, ranging from `NAmes` (225 rows) down to
  `Blueste` (2 rows) — flagged here for `/ds-validate`'s stratification decision.

## Protected/sensitive attributes

No columns encode age, gender, race/ethnicity, disability, or other protected
characteristics of a person — this dataset describes properties, not people. `Neighborhood`
is the closest thing to a proxy-for-protected-class concern (historical housing
discrimination literature ties neighborhood to race in many US cities), noted here so
`/ds-evaluate` doesn't skip the question, but there's no attribute in this dataset from
which to actually compute a fairness slice by a protected class — `Neighborhood` is
retained here purely as a price-relevant feature, evaluated as a slice for reliability
(sample size), not as a fairness slice.

## Open questions for the stakeholder

- Confirm whether `LotFrontage`'s missing 259 rows should be imputed from
  neighborhood medians (as `/ds-prep` proposes) or flagged to the pricing agent as
  "unknown lot frontage" at inference time.
- Confirm the 2010 cutoff (data ends July 2010) doesn't already meaningfully misprice
  today's Ames market — this is a historical benchmark dataset, not live data; a real
  deployment would need a current retrain, out of scope for this benchmark run.
