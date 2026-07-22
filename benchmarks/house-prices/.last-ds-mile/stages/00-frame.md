# Stage 0 — Problem Framing

## Problem statement

Ames, Iowa residential sale prices, 2006–2010 (the Kaggle "House Prices — Advanced
Regression Techniques" dataset). A listing-price advisory tool for a residential
brokerage: given a home's characteristics, produce a suggested listing price before
the home goes on the market.

## Decision this feeds

A pricing agent uses the suggested price as the anchor for the initial listing —
raising it, lowering it, or accepting it based on local knowledge the model doesn't
have. This is decision support, not price-setting: the agent always has override
authority. Today, without this tool, agents price by comparables pulled manually,
which is slow and inconsistent across agents with different levels of experience.

## Unit of analysis and target

One row = one single-family residential sale in Ames, Iowa, closed between January
2006 and July 2010. Target: `SalePrice`, the closed sale price in USD. Two people
given the same raw row would compute this identically — it's a direct column, not a
derived definition.

## Do we even need ML?

A simple median-by-neighborhood lookup was considered as the "do we even need ML"
check (see `/ds-baseline` below, which formalizes this). Neighborhood alone leaves
substantial within-neighborhood price variation unexplained (`OverallQual`,
`GrLivArea`, and age visibly move price within any single neighborhood — confirmed
in `/ds-explore`), so a model that combines multiple features is justified, but the
baseline stays the reference point every model must beat by more than noise (see
`uncertainty-quantification`).

## Success metric

**RMSE of `log(SalePrice)`.** Chosen over raw-dollar RMSE because `SalePrice` spans
multiple orders of magnitude ($34,900–$755,000) — see `metric-selection`'s regression
table: a scale-appropriate log transform keeps a $50k miss on a $700k home from
swamping a $5k miss on a $100k home in the loss. This is also the actual Kaggle
competition metric, which matters for benchmarking this run's numbers against a known
leaderboard.

**Business framing of the metric:** an agent's own manual pricing typically lands
within roughly 10–15% of eventual sale price (informal internal estimate, not
measured here) — so this project's bar for "worth deploying" is a log-RMSE
corresponding to a typical error meaningfully tighter than that range, not simply
"beats zero."

## Non-goals

- Not a valuation for commercial, multi-family, or non-Ames properties.
- Not a substitute for a licensed appraisal — this is a listing-price *suggestion*,
  not a legal valuation.
- Not forecasting future market conditions beyond the 2006–2010 window represented in
  training data (see `/ds-validate`'s distribution-shift check for how this project
  treats that boundary).
