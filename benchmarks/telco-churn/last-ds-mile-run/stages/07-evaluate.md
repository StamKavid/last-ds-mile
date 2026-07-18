# 07 — Evaluation & Error Analysis

**Metric confirmed:** ROC-AUC, as chosen in `00-frame.md`. Overall sealed AUC (from
`/ds-open`, `LEDGER.md`): **0.8471** — up from an earlier re-seal's 0.8268 (see
`06-model.md`): the stratified-split fix landed between the two runs and changed which
rows land in dev vs. held, a genuinely different sample, not just re-measurement noise.

**Mechanism gap found and closed while re-running this stage:** the calibration and
slice findings below require the true held-set labels, but `sealed_bet.score.open_seal()`
used to only return an aggregate `{sealed_score, baseline, sigma, lift, shipped}` dict —
never per-row predictions or labels — even though this exact stage's own `SKILL.md`
instructs producing a calibration check and slice table "on the held set." `open_seal()`
now calls a new `sealed_bet.score.reveal()`, which writes `held/revealed.csv` (the true
target plus the submitted predictions, joinable with the already-readable
`held/features.csv` by row order) as soon as the seal is opened — legitimate because the
one-look guarantee has already been spent by that point; `reveal()` refuses to run before
opening.

**Calibration — genuinely good, worth reporting positively:** predicted-probability
deciles track actual churn rate closely across the full range (top decile: mean
predicted 0.742 vs. actual 0.743; bottom decile: 0.017 vs. 0.007 — slightly
over-confident at the very bottom, but the gap closes fast by decile 2). A retention team
can read this model's output as an approximate real probability, not just a ranking. See
`figures/07-calibration.png` for the full decile curve against a perfect-calibration
reference line.

**Slice performance — by `Contract` type (the real finding of this stage, and the finding
itself changed after the stratified-split re-seal — see note below):**

| Contract | n | AUC (within-slice) | Churn rate |
|---|---|---|---|
| One year | 308 | 0.7703 | 13.0% |
| Two year | 352 | 0.7585 | 2.8% |
| Month-to-month | 749 | 0.7504 | 43.3% |

See `figures/07-slice-performance.png` for the same comparison against the overall AUC.

**This flipped from the previous re-seal, and that's worth being honest about, not
smoothing over:** the pre-stratification run found `One year` the *hardest* slice
(AUC 0.6805) and `Two year` the easiest; this run — same model family, same feature set,
same iteration framings, a different (stratified) dev/held sample — finds `One year` the
*easiest* slice and `Month-to-month` the hardest. Within-slice AUC (0.75–0.77) is still
notably lower than the overall 0.8471 in both versions of this finding, for the same
underlying reason: `Contract` itself is one of the two strongest overall drivers
(`02-explore.md`, `08-explain.md`), so a large share of the overall AUC comes from
correctly separating month-to-month customers (who churn a lot) from two-year customers
(who almost never do) — once you're already inside one contract-type slice, that easy
signal is gone. But *which* slice is hardest turns out to be sensitive to exactly which
289-ish held rows you draw, at this sample size (308–749 rows per slice) — a genuine
instability worth flagging to a stakeholder rather than presenting either version as a
settled fact. **Reporting only the overall 0.8471 without any slice breakdown would
overstate how well the model discriminates among otherwise-similar customers** — that
part of the finding is stable across both re-seals, even if the specific ranking isn't.

**Error analysis:** no single slice is decisively "the" hard one this time (0.75–0.77
across all three, a narrower spread than the previous re-seal's 0.68–0.76) — plausibly
because the stratified split simply drew a sample where the three segments' remaining,
non-`Contract` signal is more evenly matched. Treat any single re-seal's "hardest slice"
claim as informative but not load-bearing on its own; the stable conclusion is that
within-slice performance is meaningfully below the aggregate, not which specific slice is
worst.
