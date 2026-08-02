# 01 — Data Understanding

## Shape & types
- 284,807 rows × 31 columns. 30 `float64` (`Time`, `V1`-`V28`, `Amount`), 1 `int64` (`Class`).
- No missing values anywhere.

## Class balance
- Genuine (0): 284,315 (99.827%)
- Fraud (1): 492 (0.173%)
- Severe imbalance — confirms accuracy is unusable as a metric (per `00-frame.md`).

## Time
- `Time` = seconds since first transaction, spans 0 to 172,792s (~48 hours / 2 days).
  Monotonic transaction order, not wall-clock (no date/day-of-week recoverable).

## Amount
- Right-skewed: median $22, mean $88, max $25,691, min $0. Will need scaling
  (fraud amounts aren't necessarily large — checked in `02-explore.md`).

## Data quality issue found: duplicate rows

**1,081 exact-duplicate rows** (`df.duplicated().sum()`), of which **19 are fraud**
(out of 492 total fraud rows — ~4% of all fraud cases are duplicated) and ~1,062 are
genuine.

This matters for validation: `V1`-`V28` are continuous PCA float values — two
transactions matching exactly across all 28 components by coincidence is
essentially impossible. These are almost certainly the same underlying transaction
recorded twice (or a known artifact of this public dataset), not independent
observations. If left in and split randomly between train/test, the same transaction
could appear in both, letting the model "memorize" it — inflating test performance.
**Action: drop duplicates before splitting** (handled in `03-prep.md`).

## Do we need external data / joins?
No — single flat file, no keys to join, no external sources needed or available
(features are already anonymized/PCA'd upstream).
