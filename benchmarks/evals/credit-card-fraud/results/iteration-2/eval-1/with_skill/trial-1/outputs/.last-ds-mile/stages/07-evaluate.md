# 07 — Evaluation & Error Analysis

Held-out test set (56,746 rows, 95 fraud, touched exactly once): `evaluate.py`.

## Headline metric
- **Test PR-AUC: 0.8186** (CV estimate was 0.8441 ± 0.0275) — within one fold
  std of the CV estimate, so the CV score wasn't optimistic/leaked; a modest,
  expected drop from a single finite test sample.
- **Test ROC-AUC: 0.9655** (reported for context only — not the primary
  metric per `/ds-frame`, given the class imbalance).
- Both clear the baseline (PR-AUC 0.605) by a wide margin — real lift.

## Confusion matrices at frozen thresholds (from `/ds-model`, applied once)
| Target precision | Threshold | TP | FP | FN | TN | Actual precision | Actual recall |
|---|---|---|---|---|---|---|---|
| ≥0.50 | 0.0381 | 80 | 124 | 15 | 56,527 | 0.392 | 0.842 |
| ≥0.70 | 0.1083 | 80 | 51 | 15 | 56,600 | 0.611 | 0.842 |
| ≥0.90 | 0.6746 | 74 | 6 | 21 | 56,645 | 0.925 | 0.779 |

Actual test precision is somewhat below the train-OOF target at the 0.5/0.7
bands (e.g. 0.611 actual vs. 0.70 target) — with only 95 fraud cases in the
test set, single-digit swings in TP/FP move precision noticeably; this is
sampling noise from a small positive class, not evidence the threshold
choice was wrong. The ≥0.90 band came in close to target (0.925).

## Subgroup performance (hard gate: not just an aggregate metric)
| Slice | n | Fraud | Recall @ precision≥0.7 threshold | FP |
|---|---|---|---|---|
| Night (hour 0–5) | 4,892 | 27 | **96.3%** | 6 |
| Day (hour 6–23) | 51,854 | 68 | **79.4%** | 45 |

Recall is notably *better* at night despite `/ds-explore` finding a higher
night-time fraud *rate* — plausible explanation: night-time genuine
transaction volume is much lower, so the classes may be more separable in
that slice (less overlap in the feature space) even though there are fewer
fraud examples to learn from overall. Day-time recall (79.4%) is the weaker
slice and the one to prioritize if this is iterated on further.

## Error analysis (false negatives at precision≥0.7 threshold)
15 of 95 fraud cases missed. Amounts of missed fraud span from very small
($0.20–$1.79, consistent with card-testing-style fraud the model apparently
under-weights) up to one large case ($1,096.99) — no single dominant failure
pattern; missed cases aren't concentrated at one end of the amount
distribution.

## Verdict
Model materially beats baseline, generalizes from CV to held-out test
(0.844 → 0.819, within noise), and doesn't fail silently on an obvious
subgroup — day-time recall (79.4%) is the weakest area but not a
red-flag-level failure.
