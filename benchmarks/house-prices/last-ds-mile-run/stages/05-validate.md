# 05 — Validation Design

**Time dimension check — yes, and it matters here.** This dataset spans 2006–2010,
which includes the US housing-market downturn. Checked whether this is more than a
theoretical concern before choosing: median `SalePrice` moves from $167,000 (2007) to
$155,000 (2010) — a real ~7% drift, not noise. A production AVM is deployed to predict
**future** sales from **past** training data; a random/shuffled split would let the model
train on some 2010 (post-drift) sales while being validated on some 2006–2008
(pre-drift) sales it wouldn't have had access to in real deployment, understating the
real generalization gap. Per `ds-method`'s Red Flag ("validation metric beats the
training metric" / shuffled-temporal-split failure mode — see
`lessons/the-leaderboard-that-lied.md`), this is exactly the setup that produces an
optimistic backtest.

**Groups check:** no — nothing in this dataset indicates the same physical property
appears more than once (no repeat-sale/parcel-ID column), so no group-leakage concern.

**Imbalance check:** not applicable — this is a regression target.

**Chosen strategy: time-based split**, ordered by `sale_period = YrSold*12 + MoSold`
(`MoSold`/`YrSold` are used *only* as the sort key for the split boundary — they are
excluded from the feature set per `03-prep.md`'s leakage finding, so the model itself
never sees them). Held rows are always strictly later in time than dev rows, matching
`sealed_bet.splits.split(strategy="time", time_col=...)`'s existing semantics (verified
in Phase A's own test suite: ties at the boundary land entirely in dev, never split
across both sides).

**Exact split call, reused identically by `/ds-seal`:**
```python
sealed_bet.seal.seal(
    data_path="prepared_with_sale_period.csv", target="log_saleprice",
    task="regression", metric="rmse", strategy="time", time_col="sale_period",
    out_dir="last-ds-mile-run", baseline_fn=neighborhood_price_per_sqft, ...,
)
```
(`out_dir` corrected here to match what this run actually used —
`benchmarks/house-prices/last-ds-mile-run`, not `.last-ds-mile` — since every skill
hardcodes the latter path, which is also blanket-`.gitignore`d, so a committed benchmark
has to use a different directory name to keep its evidence out of the ignore rule. See
`BENCHMARKS.md` for this as its own product gap.)

**Verified after sealing — split-adversary probe fires a false positive here, by
design:** `sealed_bet.adversary.split_adversary` (see `sealed_bet/seal.py`) certifies
that dev and held are statistically indistinguishable, which is the right check for a
`random` split (Telco's `05-validate.md` shows it passing cleanly there). For a *time*
split it is expected to fail — dev and held are deliberately different (held is always
strictly later), which is the entire point of choosing this strategy in the first place.
Here it reports train-vs-held AUC 0.887 (lift 35.3σ, "⚠ SUSPECT"), which is not evidence
of a leak; it is evidence the split-adversary's certification only means something for a
`random`/`group` split and should be read as N/A rather than failing for `time`. Noted
for `BENCHMARKS.md` as a real product gap (the probe should skip or re-frame its verdict
for `strategy="time"`), not something fixed in this run.

**Architecture finding worth flagging (not a blocker for this run, but a real gap):**
`sealed_bet.seal()` always builds `feature_cols` as *every* non-target column in the CSV
— there's no way to tell it "split by this time column, but don't feed it to the model."
That's fine here specifically because `sale_period` (a coarse "current calendar month"
signal) is itself legitimately known at prediction time — it's not the same leakage class
as `SaleType`/`SaleCondition` (outcome-of-the-sale fields, already excluded in
`03-prep.md`). But it means: if a future user's `time_col` were something that *shouldn't*
be a model input (e.g. a raw future-looking timestamp with no standalone predictive
legitimacy), `seal()` would silently feed it to the model anyway. Noted for
`BENCHMARKS.md` as a real product gap surfaced by this dogfood run, not something fixed
here (out of scope for a benchmark exercise, not a code change).
