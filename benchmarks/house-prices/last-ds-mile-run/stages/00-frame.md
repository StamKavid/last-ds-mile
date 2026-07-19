# 00 — Problem Framing

**Source:** Kaggle "House Prices: Advanced Regression Techniques" (Ames, Iowa residential
sales, De Cock 2011). Public competition — used here as a real, external benchmark since
Kaggle publishes community leaderboard characteristics for this exact problem.

**Decision this feeds:** A hypothetical automated valuation model (AVM) a real-estate
platform would use to show a "suggested list price" to a seller before they set an
asking price. Wrong in either direction has a concrete cost: too high stalls the listing
(days-on-market cost), too low leaves money on the table (opportunity cost).

**Unit of analysis:** One residential property sale in Ames, Iowa, sold 2006–2010.

**Target definition:** `SalePrice` — the final closing sale price in USD, as recorded in
the Ames Assessor's Office data. Modeled as `log1p(SalePrice)` (matching Kaggle's own
scoring convention for this competition) since raw `SalePrice` is right-skewed
(skew = 1.88) and this is a multiplicative, not additive, error problem — a $10k miss on
a $50k starter home and a $10k miss on a $500k house are not equally bad.

**Do we even need ML?** A simple $/sqft-by-neighborhood lookup is the realistic
non-ML alternative and is exactly what `/ds-baseline` will quantify — if a model can't
beat that by a meaningful margin, it isn't earning its complexity. (Not yet run; see
`04-baseline.md`.)

**Success metric:** RMSE of `log1p(SalePrice)` — the exact metric Kaggle scores this
competition on, chosen here specifically so this run's Sealed Bet result is comparable to
publicly known leaderboard characteristics for the same metric on the same problem.

**Non-goals:** No claim this generalizes beyond Ames, Iowa or beyond the 2006–2010 sale
window; no attempt to beat the literal Kaggle leaderboard (which is widely understood in
the Kaggle community to include heavily leaked/overfit-to-public-test submissions after
years of the test labels being effectively public — see `04-baseline.md` and
`BENCHMARKS.md` for that caveat). The comparison point here is "a genuinely honest model,
scored the same way," not "rank #1."
