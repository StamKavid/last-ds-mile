# 07 — Evaluation & Error Analysis

Best model: Random Forest (`class_weight="balanced"`), evaluated on the temporal
holdout (last 30% by `Time`, 85,118 rows, 107 fraud).

## Headline metrics
- **PR-AUC: 0.814** vs. baseline 0.0013 — large, real lift.
- **ROC-AUC: 0.959**.

## Precision/recall tradeoff (this is the operating decision left open in `00-frame.md`)
| Target recall | Precision at that recall | Threshold |
|---|---|---|
| ~70% | 98.7% | 0.453 |
| ~80% | 47.5% | 0.033 |
| ~90% | 6.3% | 0.007 |
| ~93% | 2.0% | 0.003 |

There's a sharp cliff between recall 70% and 80%: precision falls from 99% to 48%.
Practically, this model can catch ~70% of fraud while almost never crying wolf
(1 false alarm per ~77 flags), but pushing further to catch 80%+ means accepting
roughly 1 correct flag for every 1 false one. **Which side of that cliff to operate
on depends on the unresolved cost tradeoff from `00-frame.md`** — I can't pick for
you without knowing the $ cost of a missed fraud vs. a wrongly-flagged transaction.

At the default 0.5 threshold: precision 100%, recall 67.3% (72/107 fraud caught, 0
false alarms, 35 missed).

## Subgroup performance (hard gate — not just the aggregate number)
Recall by transaction-amount quartile, threshold=0.5:

| Amount range | n | fraud | precision | recall |
|---|---|---|---|---|
| $0–$5 | 21,591 | 53 | 100% | 71.7% |
| $5–$20 | 21,437 | 11 | 100% | **36.4%** |
| $20–$73 | 20,810 | 10 | 100% | 70.0% |
| $73–$25,691 | 21,280 | 33 | 100% | 69.7% |

**Finding**: the model misses fraud disproportionately in the $5–$20 bucket (recall
36% vs ~70% everywhere else) — only 11 fraud cases in that bucket in the test set, so
this could be noise from a small sample, but it's consistent enough (least by more
than half) that it's worth flagging rather than averaging away. Precision holds at
100% in every bucket at this threshold, so the weakness is specifically about missed
low-to-mid-value fraud, not about false alarms concentrating anywhere.

## Error analysis
- **False negatives** (35 at threshold 0.5): concentrated somewhat in the low-amount
  buckets per above.
- **False positives**: zero at threshold 0.5, so no pattern to analyze at this
  threshold; they appear once the threshold is lowered to chase higher recall (see
  table above).
- No leakage red flag observed: performance on the CV folds (0.851 mean) and the
  temporal holdout (0.814) are close, and the small gap is explained by the known
  fraud-rate shift, not by a validation-set-beats-training-set anomaly.

## Sample-size caveat
Only 107 fraud cases in the test set (and 11–53 per subgroup). Point estimates above
— especially the subgroup recall numbers — should be read with real uncertainty, not
as precise population values.
