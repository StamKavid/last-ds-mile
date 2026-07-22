# Stage 7 — Evaluation & Error Analysis

## Metric confirmation, with spread

Reporting **ROC-AUC**, the exact metric chosen in `/ds-frame`. Computed via true
out-of-fold predictions of the shipped `Blend(LogReg+CatBoost-native)`.

**Overall out-of-fold ROC-AUC: 0.8475** (pooled) / **0.8477 ± 0.0113** (fold mean),
matching `/ds-model` exactly — and matching seed=42's row in the 5-seed reliability
check to 4 decimal places, a cross-run consistency confirmation, not just an internal
one. PR-AUC 0.6650, reported as the stricter secondary check.

## Calibration check

![Calibration by predicted-score decile](../.last-ds-mile/figures/07-calibration.png)

**The Blend's raw scores are not well-calibrated as literal probabilities, even
though ranking (AUC) is solid.** The observed curve sits visibly below the perfect-
calibration diagonal across most of the range — e.g. at decile 5, mean predicted
score is 0.443 but actual churn rate is only 0.224. **The model systematically
over-states churn probability** in the middle of its score range. This doesn't
affect the frozen-threshold deployment decision (thresholding is a ranking
operation, unaffected by miscalibration), but it would matter for any downstream use
that treats the raw score as a true probability (e.g. expected-revenue-at-risk
calculations) — that use case would need the score recalibrated (isotonic
regression or Platt scaling) first, stated explicitly here rather than left as a
silent trap for a future consumer of this score.

## Slice performance — by Contract type

| Contract | n | Churn rate | ROC-AUC |
|---|---|---|---|
| Month-to-month | 3,875 | 42.7% | 0.758 |
| One year | 1,473 | 11.3% | 0.714 |
| Two year | 1,695 | 2.8% | 0.733 |

![Slice performance vs overall](../.last-ds-mile/figures/07-slice-performance.png)

**Every contract-type slice scores below the overall ROC-AUC (0.848).** This is a
real, generalizable finding, not a fluke of one slice: the model discriminates well
*between* contract types (that's most of where its overall AUC comes from — see
`/ds-explain`) but discriminates *less* well *within* any single contract type,
where every customer already shares the dominant risk factor. One-year and two-year
counts are smaller (166 and 48 churners respectively), so their specific ROC-AUC
values carry more sampling noise than month-to-month's; the *direction* (worse than
overall) is consistent across all three regardless.

## Slice performance — by tenure bucket

| Tenure | n | Churn rate | ROC-AUC |
|---|---|---|---|
| 0–6 months | 1,481 | 52.9% | 0.774 |
| 7–12 months | 705 | 35.9% | 0.798 |
| 13–24 months | 1,024 | 28.7% | 0.806 |
| 25–48 months | 1,594 | 20.4% | 0.800 |
| 49+ months | 2,239 | 9.5% | **0.813** |

A modest, sensible pattern: the model discriminates slightly better for longer-
tenured customers, who have more behavioral history for the model to learn from;
newest customers (0–6 months) are the hardest to call, though the gap (0.774 vs.
0.813) is small relative to the model's own fold-to-fold std (0.0113).

## Slice performance — by InternetService

| Service | n | Churn rate | ROC-AUC |
|---|---|---|---|
| DSL | 2,421 | 19.0% | 0.812 |
| Fiber optic | 3,096 | 41.9% | 0.794 |
| No internet | 1,526 | 7.4% | **0.846** |

**Fiber-optic customers — the highest-risk segment — have the model's worst
within-segment discrimination (0.794)**, the same "harder to discriminate within
the highest-risk group" pattern found for `Contract` above. This is the segment
where retention-outreach targeting would benefit most from a better feature (a
service-quality or competitor-price signal isn't in this dataset) — named as a real
limitation, not glossed over because the segment's *overall* risk is already known.

## Error analysis — missed churners (false negatives) at the frozen threshold

175 churners missed at threshold 0.3338. **The lowest-scored misses (furthest from
being caught) are long-tenured (53–72 months), two-year-contract customers with
low-to-moderate monthly charges** — customers whose entire feature profile says
"loyal, low-risk," who churned anyway. This is a genuinely hard-to-predict pattern
(no feature in this dataset explains an otherwise-loyal-looking customer's
departure) rather than a fixable gap in the current features.

## Error analysis — false alarms (false positives)

2,100 false alarms at the frozen threshold. **The highest-scored false alarms are
very-short-tenure (1–3 months), month-to-month customers with high monthly
charges** — exactly the textbook high-risk profile, who simply didn't churn within
this snapshot's observed window. Not a model failure so much as the ceiling of a
moderate-effect-size problem: a customer matching every risk factor still churns at
well under 100% (`/ds-explore`'s Contract slice shows even month-to-month churns at
"only" 42.7%, not near-certainty).
