# 04 — Honest Baseline

## Baseline definition

Majority-class / prior-probability baseline: always predict "genuine"
(score every transaction with the constant fraud prevalence, 0.1667%,
computed on the deduplicated dataset — 473 fraud / 283,726 rows).

No informal single-rule heuristic exists for this problem (no prior fraud
system in place to benchmark against), so majority-class is the correct
dumbest-possible anchor per `ds-baseline`.

## Baseline score (using the exact metrics from `/ds-frame`)

| Metric | Baseline value |
|---|---|
| **PR-AUC (average precision)** — primary metric | **0.00167** (equals prevalence — mathematically the floor for any classifier) |
| ROC-AUC | 0.500 (uninformative by construction) |
| Precision at hard 0/1 prediction | 0.0 (never predicts fraud) |
| Recall at hard 0/1 prediction | 0.0 (catches zero fraud) |
| Accuracy | 99.83% — **explicitly not the metric we're using**, included only to make concrete why accuracy is the wrong lens: this "dumb" baseline already looks 99.83% accurate. |

## What "beating it" concretely means

- Any real model must clear **PR-AUC ≫ 0.00167** — even a PR-AUC of 0.10
  (10x the floor) would sound unremarkable in absolute terms but is
  actually 60x the baseline lift.
- The 99.83% accuracy figure must never be cited as evidence of a working
  model — it's within 0.17 points of what predicting nothing achieves.
- `/ds-model` candidates are judged against 0.00167 PR-AUC as the anchor,
  not against 0 or against "looks good."
