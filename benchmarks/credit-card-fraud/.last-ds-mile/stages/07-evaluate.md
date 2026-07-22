# Stage 7 — Evaluation & Error Analysis

## Metric confirmation, with spread

Reporting **PR-AUC**, the exact metric chosen in `/ds-frame`. Computed via true
out-of-fold predictions of the shipped `Blend(LightGBM+CatBoost)`.

**Overall out-of-fold PR-AUC: 0.8451** (pooled) / **0.8455 ± 0.0117** (fold mean),
matching `/ds-model` exactly. ROC-AUC 0.9804, reported as the secondary check only.

## Calibration check

![Calibration by predicted-score decile](../figures/07-calibration.png)

The bottom 9 deciles correctly cluster near-zero (the model assigns near-zero fraud
probability to the overwhelming bulk of genuine transactions, as it should). The top
decile is where the real signal lives: mean predicted score **0.0212** vs. actual
fraud rate **0.0158** — **the model is somewhat over-confident even in its
highest-risk decile.** This matters if anyone downstream wants to treat the raw score
as a literal probability (e.g. multiplying by transaction value for an
expected-loss estimate) — for that use case, the score would need recalibration
(e.g. isotonic regression); for the actual deployment decision (rank-and-threshold),
this miscalibration doesn't matter, since it doesn't change which transactions
rank above the frozen threshold.

## Slice performance — by transaction-amount bucket

| Bucket | n | n_fraud | PR-AUC |
|---|---|---|---|
| <$10 | 99,821 | 238 | 0.859 |
| $10–50 | 90,327 | 55 | 0.762 |
| $50–200 | 64,808 | 98 | **0.928** |
| $200–1000 | 25,835 | 73 | 0.742 |
| >$1000 | 2,935 | 9 | 0.780 |

![Slice performance vs overall](../figures/07-slice-performance.png)

No clean monotonic pattern — best at $50–200, worse at both smaller and larger
amounts. **Caution stated explicitly**: several buckets have under 100 fraud
examples (as few as 9 in the >$1000 bucket), so bucket-to-bucket PR-AUC differences
here carry real sampling noise on top of any genuine effect — this is reported as a
directional finding, not a precise ranking of amount-bucket difficulty.

## Slice performance — by time-of-day period

| Period | n | n_fraud | Fraud rate | PR-AUC |
|---|---|---|---|---|
| Night (0–5) | 23,842 | 115 | 0.48% | **0.918** |
| Morning (6–11) | 70,643 | 118 | 0.17% | 0.896 |
| Afternoon (12–17) | 96,121 | 133 | 0.14% | 0.816 |
| Evening (18–23) | 93,120 | 107 | 0.11% | **0.754** |

**A real, sensible pattern**: the model performs *best* during overnight hours,
where `/ds-explore` found the fraud rate is highest (0.48% vs. 0.11–0.17% elsewhere)
— more, cleaner positive examples per volume gives the model more to learn from.
Performance is *worst* during evening hours, the lowest-fraud-rate period, where
each genuine fraud case is more of a needle in a larger haystack. This is a
coherent, explainable pattern, not a puzzling anomaly.

## Error analysis — missed fraud (false negatives) at the frozen threshold

80 fraud cases missed at threshold 0.4932. **The highest-scored misses (closest to
being caught) are overwhelmingly small-dollar transactions** ($0–$7 dominate the
top of the missed list) — consistent with `/ds-explore`'s finding that fraud trends
toward smaller amounts: a small fraudulent "test" transaction is genuinely hard to
distinguish from the overwhelming majority of small genuine purchases using these
features alone. This is a named, structural limitation, not a vague "the model
misses some fraud."

## Error analysis — false alarms (false positives)

Only 51 total. The highest-scored false alarms sit at score ≈0.9999 — the model was
maximally confident and still wrong on a handful of genuine transactions. With only
51 cases this isn't a systemic pattern worth deeper slicing; noted as the honest
cost side of the frozen threshold's 83.1% recall.
