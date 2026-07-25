# 01 — Data Understanding

## Provenance / trust

Single flat CSV (`creditcard.csv`, 143.8 MB, 284,807 rows × 31 columns),
plain text, no executable content. No pickle/joblib/deserialization risk.
Values are numeric only — scanned for non-numeric anomalies during load;
none found. This is the well-known public "Credit Card Fraud Detection"
dataset (European cardholders, September 2013, 2 days of transactions),
recognizable from its exact shape and PCA'd `V1`-`V28` schema.

## Data dictionary

| Column | Type | Meaning | Known issues |
|---|---|---|---|
| `Time` | float | Seconds elapsed since the first transaction in the dataset (0 to 172,792 ≈ 48 hours) | Not a wall-clock timestamp; only relative ordering/spacing is meaningful. |
| `V1`–`V28` | float | Principal components from a PCA transform of the original (undisclosed) transaction features, applied by the dataset providers for confidentiality | Original meaning is unrecoverable. Already roughly centered; scales vary per component (see ranges below). |
| `Amount` | float | Transaction amount | Range $0–$25,691.16; 1,825 rows have `Amount == 0` (flagged below, not dropped). |
| `Class` | int (0/1) | Target: 1 = fraud, 0 = genuine | No missing/ambiguous values. |

## Integrity findings

- **Missingness**: zero missing values across all 31 columns.
- **Duplicate rows**: 1,081 exact duplicate rows (1,854 rows involved once
  both copies are counted), of which 19 duplicate rows are fraud (`Class==1`).
  **Flagged, not dropped here** — decision on whether/how to deduplicate
  belongs to `/ds-prep`, but this is also a **validation-split concern**:
  if duplicates aren't deduplicated (or are but a duplicate pair still ends
  up split across train/test), the same transaction could appear in both
  train and test, inflating apparent performance. Must be handled before
  `/ds-validate` finalizes the split.
- **`Amount == 0`**: 1,825 rows (0.6%) have zero amount. Plausible for
  real transactions (auth-only/reversed charges); not dropping, not
  imputing — kept as-is and noted in case it correlates with fraud rate
  (checked in `/ds-explore`).
- **Class balance**: severe imbalance — 492 fraud / 284,315 genuine
  (0.173% positive rate). This drives metric choice (`/ds-frame`) and
  resampling/weighting decisions (`/ds-model`).
- **`Time` is not wall-clock**: only spans ~48 hours and is seconds-since-
  start, not a real timestamp — no day-of-week/seasonality signal is
  extractable from it, only intra-window recency/position.
- **No implausible values** found in `describe()` ranges for any column
  (PCA components have wide but not physically-impossible ranges;
  `Amount` max of $25,691 is high but plausible for a real transaction).
- **No secrets/PII-looking columns** — all features are numeric and
  anonymized by design.

## Open questions for stakeholder (unanswered — proceeding with defaults)

- Are the 1,081 duplicate rows genuine repeated transactions (e.g. retries)
  or a data-collection artifact? Default assumption: artifact of the PCA
  anonymization process (documented publicly for this dataset) — will
  deduplicate in `/ds-prep` and confirm split integrity in `/ds-validate`.
- No other stakeholder-only questions remain; the dataset is otherwise
  self-contained and numeric.
