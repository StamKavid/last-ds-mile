# 03 — Prep

## Cleaning
- Drop the 1,081 exact-duplicate rows identified in `01-data.md` (keep first
  occurrence). This removes 19 duplicated fraud rows and ~1,062 duplicated genuine
  rows, leaving 283,726 rows (473 fraud, 283,253 genuine — fraud rate 0.1667%,
  barely changed).
- No missing values to impute.

## Feature engineering
- `V1`-`V28`: used as-is — already PCA-transformed and roughly standardized upstream;
  no further transform needed, and no way to build domain features from anonymized
  components.
- `Amount`: scaled with `RobustScaler` (median/IQR) rather than `StandardScaler`,
  since `Amount` is heavily right-skewed with extreme outliers ($25,691 max vs $22
  median) that would dominate a mean/std scaler.
- `Time`: scaled the same way. Kept as a raw numeric feature (elapsed seconds) — not
  decomposed into hour-of-day because `02-explore.md` found only a weak, possibly
  noisy time effect over just 2 days, not worth manufacturing a categorical from.
- Scalers are fit on the training split only and applied to test — fitting on the
  full dataset before splitting would leak test-set distribution info into training
  (a classic case the `target-leakage-detection` skill flags).

## Leakage check
No feature is derived from `Class` or from post-outcome information (chargeback
status, review outcome, etc. — none of that exists in this file). The only leakage
vector identified was the duplicate-row issue (same transaction in both splits),
handled by deduplication above.
