# 05 — Validation Design

**Time dimension check:** no — this is a cross-sectional account snapshot, not a
sequence of dated events. `tenure` is a duration (months as of the snapshot), not a
timestamp to split on. Random split is appropriate.

**Groups check:** no — one row per customer account, no repeated-entity structure.

**Imbalance check — yes, real (26.5% churn):** flagged as a genuine consideration, not
skipped. **Product gap found here, since fixed:** `sealed_bet.splits.split(strategy="random")`
originally did a plain `train_test_split(..., shuffle=True)` with no stratification
option. This dataset's moderate imbalance and decent sample size (7,043 rows) meant a
plain random split was very unlikely to produce a badly skewed held set by chance — the
first seal of this run verified held-set churn rate 26.1% vs. dev-set 26.6%, close enough
that the lack of stratification made no practical difference — but it was a real, current
limitation for any more severely imbalanced problem (see the Credit Card Fraud case,
where this same gap would not have been a minor caveat; see `BENCHMARKS.md`). Fixed:
`sealed_bet.splits.split(stratify_col=...)`, and a policy function
`auto_stratify_col(task, strategy, target)` that `seal()` now calls automatically for any
classification target on a `random` split — no flag needed. This benchmark was re-sealed
after that fix landed, so the dev/held split committed here is the stratified one, not
the originally-verified unstratified one; the baseline/sealed numbers in `04-baseline.md`/
`06-model.md` reflect the stratified split.

**Chosen strategy:** `strategy="random"` (the only option that fits this data's actual
structure — no time or group dimension), now automatically stratified by `Churn`.

**Exact split call, reused identically by `/ds-seal`:**
```python
sealed_bet.seal.seal(
    data_path="prepared.csv", target="Churn", task="classification", metric="roc_auc",
    strategy="random", seed=0, out_dir="last-ds-mile-run",
    baseline_fn=contract_churn_rate, ...,
)
```

**Verified after sealing — split-adversary probe:** `sealed_bet.adversary.split_adversary`
certifies dev and held are statistically indistinguishable, which is exactly what a clean
`random` split should produce. Here it reports train-vs-held AUC 0.5038 (lift 0.46σ,
below the 2σ certify threshold) — **CERTIFIED ✅** — even closer to 0.5 than the
unstratified split's 0.512, consistent with stratification making dev and held more
similar, not less. Contrast with House Prices' `05-validate.md`, where the same probe
now correctly *skips* rather than fires "SUSPECT" on a deliberate *time* split; this
dataset's `random` strategy is the case the probe is actually designed to check.
