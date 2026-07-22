# Stage 9 — Communication

## Revision note

Recomputed against the corrected `/ds-model` (`Blend(LightGBM + CatBoost-native)`,
RMSE 0.1244 ± 0.0141) and re-verified `/ds-iterate` outcome. Also adds the
cost/business-terms translation `ds-report`'s Tier 2 update now requires — doing this
arithmetic changed the recommendation itself, not just its wording (see below).

## Gate check

`.last-ds-mile/stages/07-evaluate.md` includes slice/subgroup performance (price
quintile, neighborhood) and error analysis, not only an aggregate number. Gate passed.

## Recommendation

**Deploy the pricing model as a listing-price suggestion for the pricing desk** (the
decision named in `/ds-frame`), with the agent's override authority weighted most
heavily on exactly the segment named below — this is a *stronger*, more specific
caveat than the model's raw lift-over-baseline number alone would suggest, once that
lift is translated into the same terms the pricing desk actually cares about.

## Evidence

- **Baseline comparison:** the model's cross-validated RMSE (0.1244 ± 0.0141,
  log-space) beats the flat-median baseline (0.3999) by **0.2755 — roughly 19.5x the
  model's own fold-to-fold noise.** Unambiguous, real improvement over doing nothing
  (see `/ds-model`).
- **Stability across evaluation schemes:** the CV mean (0.1244) and the one-time
  temporal holdout evaluating strictly on future sales (0.1117) are within a tight
  band, and no distribution shift was detected between training data and the Kaggle
  test population (adversarial-validation AUC 0.519 ± 0.022 — indistinguishable from
  chance; see `/ds-validate`).
- **Calibration:** negligible overall bias (mean residual −0.0001), with the bias
  concentrated at the price extremes (see limitations).
- **Drivers make sense:** `/ds-explain` found total square footage and the assessor's
  overall-quality score as the two dominant, agreeing drivers across two independent
  interpretation methods (permutation importance and SHAP), with exact top-5 agreement
  between the two methods — ordinary real-estate intuition, no leakage signal.

## Cost translation — what the metric actually means for the pricing desk

`/ds-frame` set the real bar as "meaningfully tighter than an agent's own manual
pricing, informally ~10–15% of eventual sale price" — not simply "beats a naive
baseline." Translating the RMSE into that same relative-error scale (`exp(RMSE) − 1`,
the inverse of the log transform):

| Scope | Log-RMSE | Implied typical relative error | Implied typical $ error |
|---|---|---|---|
| Overall | 0.1244 | **13.2%** | ~$21,600 at the dataset's median price ($163,500) |
| Q1 (cheapest quintile) | 0.1717 | **18.7%** | ~$19,950 at Q1's median price ($106,500) |

**This is the honest, and less flattering, version of the win than "beats the
baseline by 19.5x its noise" suggests on its own.** Overall, the model's typical
relative error (13.2%) sits inside the agent's own assumed manual-accuracy range
(10–15%) — real help, but not a dramatic beat of what an experienced agent already
does by eye. **On the cheapest quintile specifically, the model's typical relative
error (18.7%) is *worse* than the top of that assumed manual range** — meaning on
sub-$130k listings, this tool may not clearly outperform what the agent would already
produce unaided. This reframes the Q1 limitation (previously reported only in
log-RMSE terms) from "somewhat less reliable there" to **"the one segment where the
agent's own judgment should be weighted at least as heavily as the tool's suggestion,
not just moderately more than elsewhere."**

## Assumptions

- Deployment population resembles the 2006–2010 Ames training window; a real rollout
  today would need a retrain on current data (see `/ds-frame`'s non-goals).
- The agent retains override authority; this is decision support, not automated
  pricing.
- The 10–15% manual-accuracy figure is an informal internal estimate, not measured in
  this run — the cost translation above is only as reliable as that number; if a real
  measured figure exists, it should replace this estimate before this recommendation
  is finalized for actual deployment.

## Limitations (named, not implied)

1. **The model is materially less reliable on the cheapest homes, and per the cost
   translation above, may not clearly beat manual pricing there at all.** Q1
   (cheapest quintile) RMSE is 0.172 vs. 0.100–0.129 everywhere else, systematically
   over-predicting this segment (mean residual −0.055). Root cause, investigated in
   `/ds-iterate`: the cheapest quintile has a ~2.2x higher rate of non-arms-length
   sales (`SaleCondition ∈ {Abnormal, Family, Alloca}`) than the dataset overall
   (15.3% vs. 6.9%) — these sales carry idiosyncratic discounts the model can't fully
   predict even though the feature is already in the model. **Practical guidance:**
   for sub-$130k listings, treat the tool's suggestion as one input among several
   rather than the anchor, and weight it least of all if the sale appears non-arms-
   length.
2. **Two specific historical training rows are known anomalies**, not general model
   weakness: two `OverallQual=10`, `GrLivArea>4000` Edwards homes sold for far below
   what their profile predicts (documented in the dataset's own source paper as
   atypical). `/ds-iterate` tested excluding them from training against the corrected
   model; the resulting improvement (mean paired diff 0.0010) was smaller than the
   model's own fold noise (0.0141) — even smaller, proportionally, than the original
   test found — and was **not adopted**. Reported here as a tested-and-rejected fix,
   confirmed twice, not a silent non-issue.
3. **The priciest quintile is mildly under-predicted** (mean residual +0.042) — a
   smaller, roughly symmetric version of the same "extremes are harder" pattern, not
   separately investigated in this run's scope.
4. **No protected-attribute fairness gap to report** — this dataset contains no
   attribute describing a person, so no such slice exists to check (see
   `/ds-evaluate`); flagged as checked-and-not-applicable rather than skipped.
