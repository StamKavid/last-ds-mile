# Stage 1 — Data Understanding

## Sanitization gate

`creditcard.csv` is a well-known public Kaggle dataset (`V1-V28` are the *output* of
a PCA transform the original publisher applied to protect sensitive raw attributes —
provenance is documented, not an untrusted third-party pickle or notebook). No
`.pkl`/`.joblib` files were loaded from outside this workspace. No hidden-unicode or
injected-instruction scan needed — the file has no free-text columns, only numeric
PCA components, `Time`, `Amount`, and `Class`.

## Data dictionary

| Column | Type | Meaning | Notes |
|---|---|---|---|
| `Time` | numeric | Seconds elapsed since the first transaction in the dataset | Spans exactly ~2 days (172,792s); not a wall-clock timestamp |
| `V1`–`V28` | numeric | PCA-transformed features of the original (undisclosed) transaction attributes | Uninterpretable individually by design — a real, stated constraint on `/ds-explain` later, not an oversight |
| `Amount` | numeric | Transaction amount | Skew 16.98 — heavily right-tailed |
| `Class` | int (0/1) | 1 = confirmed fraud, 0 = genuine | Target |

## Integrity findings

- **No missing values** anywhere (`df.isna().sum().sum() == 0`).
- **1081 exact duplicate rows** (`df.duplicated().sum()`), of which **19 of the
  "extra" copies are fraud-labeled** (`Class == 1`). Given every feature is either a
  PCA output or a raw numeric value with no natural entity ID, an exact-duplicate row
  most plausibly reflects either a genuine repeated record in the source export or a
  PCA-collision artifact — either way, an undeduped dataset risks the *same*
  transaction landing in both a training and a validation fold, which is exactly
  `target-leakage-detection`'s train/test-contamination pattern. **Fix: deduplicated
  before any split**, in `pipeline_lib.engineer_features` (see `/ds-prep`), not inside
  a fold-specific transform, since deduplication doesn't touch the target and isn't a
  fit-requiring statistic — it's safe to do once, globally, unlike a scaler or
  encoder.
- **Class balance:** 492 fraud / 284,807 total = **0.173%** — severe imbalance,
  flagged for `imbalanced-data` and `metric-selection`.
- **No implausible values**: `Amount` min is 0 (a $0 authorization attempt, a
  plausible real transaction type — card verification holds — not an error), max
  $25,691.16 (a plausible large legitimate purchase, not out of range for a card
  network).
- **No secret-looking values** in any column (all numeric, no free text).

## Open questions for the stakeholder (would ask if this were a live engagement)

- What does a `Class=1` label's confirmation process actually look like (customer
  dispute vs. proactive bank detection)? Affects how much delay exists between
  transaction and ground-truth label, which matters for a real deployment's feedback
  loop — out of scope for this benchmark, noted rather than assumed away.
