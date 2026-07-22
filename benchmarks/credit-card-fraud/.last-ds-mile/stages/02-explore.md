# Stage 2 — EDA

## Univariate

- `Amount`: heavily right-skewed (skew 16.98), median $22.00, max $25,691.16.
- `Class`: 0.173% positive — confirmed via `value_counts(normalize=True)`, not
  assumed from the dataset's README.

## Bivariate — target relationship

**Hypothesis: fraud transactions have a distinct amount profile.** Checked directly:
fraud median amount is $9.25 vs. $22.00 for genuine — fraud trends toward *smaller*
amounts, consistent with a known real-world fraud pattern (small "test" transactions
before a larger one). This is the opposite of the naive "fraud = large amount"
assumption, and is exactly why `/ds-frame`'s "do we even need ML" check rejected a
simple amount-threshold rule.

**Hypothesis: fraud rate varies by time.** Checked by day and by hour-of-day
(`Time` mod 86400):
- By day: 0.194% (day 0) vs. 0.151% (day 1) — a mild, real drift, smaller than
  house-prices' YrSold drift but present.
- By hour-of-day: fraud rate spikes to **1.71%** at hour 2 (2-3am) — roughly **10x**
  the overall rate — concentrated in low-traffic overnight hours. **Flagged as a real,
  usable feature** (`hour_of_day`), not just a curiosity — added in `/ds-prep`.

No feature among `V1-V28` was inspected individually for a bivariate relationship —
they're PCA outputs with no interpretable meaning standalone; a per-component
correlation check would produce numbers with no way to sanity-check them against
domain knowledge, so that check is deferred to `/ds-explain`'s aggregate importance
ranking instead, where a plausibility judgment is actually possible.

## Leakage candidates flagged for `/ds-prep`

- The 1081 duplicate rows found in `/ds-data` — resolved by deduplication before any
  split (see `03-prep.md`).
- No feature among `V1-V28`, `Time`, or `Amount` is derived from `Class` or from
  another row — all are transaction-local. No leakage-shaped near-perfect
  correlations found in this pass (deferred to the post-modeling check in
  `/ds-explain`, since spot-checking 28 uninterpretable PCA components individually
  here wouldn't be actionable).
