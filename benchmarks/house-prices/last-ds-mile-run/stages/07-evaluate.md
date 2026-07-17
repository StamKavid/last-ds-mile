# 07 — Evaluation & Error Analysis

**Metric confirmed:** RMSE of `log1p(SalePrice)` — the same metric from `00-frame.md`,
not substituted. Overall sealed RMSE (from `/ds-open`, `LEDGER.md`): **0.1309**.

**Calibration:** not directly applicable in the probabilistic sense (this is a point
regression, not a probability estimate) — the relevant analogue is residual
homoscedasticity, checked via the slice table below.

**Slice performance — by actual price tier (terciles of the held set):**

| Tier | n | Price range | RMSE (log scale) |
|---|---|---|---|
| Low | 97 | $34,900 – $136,500 | **0.176** |
| Mid | 98 | $137,450 – $190,000 | 0.102 |
| High | 94 | $192,000 – $611,657 | 0.099 |

**This is the real finding of this stage, not a clean pass:** the model is meaningfully
worse on cheaper homes (RMSE 0.176, ~78% higher error than the mid tier) than on mid- or
high-priced ones. The overall 0.1309 aggregate hides this — exactly the failure mode
`ds-method`'s "one aggregate metric is enough" Red Flag warns about.

**Error analysis — worst 5 mispredictions**, all in the low-price tier, several sharing
a pattern: `IDOTRR`, `OldTown`, `Sawyer` — three of Ames's oldest, lowest-price
neighborhoods — recur among the worst misses. Hypothesis: for these homes, condition
and location-specific idiosyncrasies (deferred maintenance, lot-specific issues) that
aren't well captured by the structural features (`OverallQual`, `GrLivArea`, etc.) drive
price more than they do in mid/high-tier homes, where size and quality are more uniformly
decisive.

**Practical implication for the framed decision** (`00-frame.md`: suggested list price
before a seller sets an asking price): this model's suggested price should be shown with
lower confidence for homes in the low-price tier / older neighborhoods — carried forward
as an explicit limitation in `09-report.md`, not glossed over.
