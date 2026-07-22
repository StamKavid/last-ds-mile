# Stage 9 — Communication

## Gate check

`.last-ds-mile/stages/07-evaluate.md` includes slice/subgroup performance (Contract,
tenure bucket, InternetService) and error analysis, not only an aggregate number.
Gate passed.

## Recommendation

**Deploy `Blend(LogReg+CatBoost-native)` at the frozen threshold (0.3338) to drive
the retention team's per-cycle outreach list**, with the explicit understanding
(from the cost translation below) that this threshold trades a large volume of
unnecessary contacts for near-complete churn coverage — a deliberate choice given
`/ds-frame`'s stated cost asymmetry, not an oversight, but one the retention team's
outreach capacity needs to be sized against before rollout.

## Evidence

- **Baseline comparison:** ROC-AUC 0.8477 ± 0.0113 vs. a no-skill baseline of 0.5 —
  a lift of 0.3477, ~30.8x the model's own fold noise (see `/ds-model`).
- **Reliability confirmed across 5 independent seeds**: mean ROC-AUC 0.8477, seed-
  to-seed std **0.0004** — roughly 1/25th of the within-run fold-to-fold std
  (0.011) — this is not a lucky split.
- **In line with published benchmarks** on this dataset (~0.84–0.86 ROC-AUC for
  LogReg/XGBoost in independently published kernels) — matches, not just internally
  consistent.
- **Drivers match domain intuition directly**: `Contract` and `InternetService` are
  the top two by both interpretation methods, matching both ordinary telecom-churn
  knowledge and this run's own `/ds-explore` bivariate findings independently (see
  `/ds-explain`).

## Cost translation — what the threshold actually means for the retention team

`/ds-frame` framed this as an asymmetric-cost decision (a missed at-risk customer
costs more than one avoidable retention contact). Translating the frozen threshold's
confusion matrix into revenue terms:

| | Count | Monthly revenue |
|---|---|---|
| Churners caught (TP) | 1,694 of 1,869 (90.7%) | $127,443 of $139,131 at-risk (**91.6%**) |
| Churners missed (FN) | 175 | $11,688 |
| False alarms (FP) | 2,100 | $147,775 in monthly charges among customers who would not have churned |
| **Total contacted (TP+FP)** | **3,794** | — |

**Unlike credit-card-fraud, dollar-recall (91.6%) and case-recall (90.7%) track each
other closely here** — no meaningful skew toward missing higher- or lower-value
churners. The real number the retention team needs is the **3,794 total contacts**
this threshold generates per cycle — of which only 1,694 (44.7%) are genuine
churners. **Assumption stated explicitly, not computed**: this benchmark has no real
per-contact outreach cost or retention-offer success-rate figure, so a full dollar
ROI (cost of 3,794 contacts vs. revenue saved from retained customers) cannot be
computed here — the business would need those two inputs, and the retention team
needs to confirm 3,794 contacts/cycle is within outreach capacity, before this
threshold is finalized for production rather than adjusted toward higher precision.

## Assumptions

- This is a static snapshot, not a rolling deployment; a real rollout needs
  continuous retraining as the customer base and product mix evolve (see
  `/ds-frame`'s non-goals).
- The frozen F2 threshold assumes a missed churner costs roughly 4x more than one
  avoidable contact (F2's implicit weighting) — if the real cost ratio is less
  extreme, a higher threshold (fewer contacts, lower recall) may better match actual
  outreach capacity and retention-offer economics.

## Limitations (named, not implied)

1. **The model discriminates well between segments but less well within the
   highest-risk ones** — every `Contract` slice, and specifically the highest-churn
   `Fiber optic` `InternetService` slice, scores below the overall AUC (see
   `/ds-evaluate`). The features here explain *which group* is risky better than
   *which member of the riskiest group* will actually leave.
2. **A materially large false-alarm volume** (2,100 contacts, 55.3% of all contacts
   generated) is the direct cost of this threshold's recall-favoring choice — not a
   flaw to fix without also giving up recall, a genuine trade-off named explicitly.
3. **Raw scores overstate churn probability** in the middle of the score range
   (see `/ds-evaluate`'s calibration finding) — fine for the rank-and-threshold
   deployment here, not fine for a downstream expected-revenue-at-risk calculation
   without recalibration first.
4. **Some genuinely loyal-looking customers churn anyway** — the lowest-scored
   missed churners are long-tenured, two-year-contract, low-charge accounts with no
   feature in this dataset flagging elevated risk; not a fixable gap with the
   current feature set.
