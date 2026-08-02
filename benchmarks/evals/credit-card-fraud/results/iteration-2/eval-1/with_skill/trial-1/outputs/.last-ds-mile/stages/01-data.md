# 01 — Data Understanding

## Provenance
Single CSV (`creditcard.csv`, 143.8 MB) supplied directly by the user in the
working directory. Plain text, not a pickle/joblib — no deserialization risk,
no sanitization gate needed beyond the checks below. Column shape matches the
publicly documented Kaggle "Credit Card Fraud Detection" dataset (anonymized
European cardholder transactions, September 2013).

## Shape
- 284,807 rows × 31 columns.
- No missing values anywhere (0 nulls in every column).

## Data dictionary

| Column | Type | Meaning | Known issues |
|---|---|---|---|
| `Time` | float64 | Seconds elapsed since the first transaction in the dataset (not a timestamp/clock time). Range 0–172,792s (~48h), consistent with a 2-day capture window. | Encodes row order — must be handled carefully in validation split (see `/ds-validate`). |
| `V1`–`V28` | float64 (×28) | PCA-transformed components of the original transaction features; the publisher withheld raw features for confidentiality. | Un-interpretable individually — no domain meaning recoverable. No further feature engineering possible on these beyond what they already encode. |
| `Amount` | float64 | Transaction amount, in the original currency unit (assumed EUR per source documentation). Min 0.0, max 25,691.16, mean 88.35, std 250.12. 1,825 rows have `Amount == 0`. | Zero-amount transactions are plausible (e.g. authorization/verification transactions) — not treated as an error. No negative values. |
| `Class` | int64 | Target: `1` = fraud, `0` = genuine. Only values {0, 1} present. | 492 fraud rows (0.17%) vs. 284,315 genuine (99.83%) — extreme imbalance, addressed in `/ds-baseline` and `/ds-validate`. |

## Integrity findings
- **No missing values** in any column.
- **1,081 exact full-row duplicates** (773 rows beyond the first occurrence of
  each duplicated row, 1,854 rows total involved). This is a known
  characteristic of this public dataset. **Not dropped at this stage** — this
  is a data-understanding note, not a cleaning decision; whether/how to
  deduplicate (and whether duplicates skew the fraud rate) is deferred to
  `/ds-prep`, and duplicate leakage across train/test is a `/ds-validate`
  concern.
- `Time` and `Amount` ranges are both plausible — no negative amounts, no
  `Time` values outside the expected 2-day window.
- No implausible or out-of-domain values found; nothing resembling a secret
  (API key/token) present.

## Open questions for the stakeholder
- Are the 1,081 duplicate rows genuine repeated transactions (e.g. two
  identical small authorizations) or an artifact of how this extract was
  produced? Given `V1`–`V28` are continuous PCA floats, an exact-value
  collision across all 30 feature columns is more likely a data artifact than
  a real coincidence — flagged for `/ds-prep` to check whether duplicates are
  disproportionately fraud or genuine before deciding whether to drop them.
