# 05 — Validation Design

**Time dimension check:** no — this is a cross-sectional account snapshot, not a
sequence of dated events. `tenure` is a duration (months as of the snapshot), not a
timestamp to split on. Random split is appropriate.

**Groups check:** no — one row per customer account, no repeated-entity structure.

**Imbalance check — yes, real (26.5% churn):** flagged as a genuine consideration, not
skipped. **Real product gap found here:** `sealed_bet.splits.split(strategy="random")`
does a plain `train_test_split(..., shuffle=True)` with no stratification option — only
`random`/`group`/`time` strategies exist, none of them class-balance-aware. For this
dataset's moderate imbalance and decent sample size (7,043 rows), a plain random split
is very unlikely to produce a badly skewed held set by chance (verified after sealing:
see `BENCHMARKS.md`), so this doesn't block the run — but it's a real, current
limitation for any more severely imbalanced problem (see the Credit Card Fraud case,
where this same gap is not a minor caveat). **Verified after sealing:** held-set churn
rate 26.1% vs. dev-set 26.6% — close enough that the lack of stratification made no
practical difference here.

**Chosen strategy:** `strategy="random"` (the only option that fits this data's actual
structure — no time or group dimension), accepting the noted stratification gap as a
documented, verified-non-fatal limitation for this specific dataset's imbalance level.

**Exact split call, reused identically by `/ds-seal`:**
```python
sealed_bet.seal.seal(
    data_path="prepared.csv", target="Churn", task="classification", metric="roc_auc",
    strategy="random", seed=0, out_dir="last-ds-mile-run", ...,
)
```
