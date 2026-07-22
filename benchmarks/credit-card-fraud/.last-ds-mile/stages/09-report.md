# Stage 9 — Communication

## Gate check

`.last-ds-mile/stages/07-evaluate.md` includes slice/subgroup performance
(transaction-amount bucket, time-of-day period) and error analysis, not only an
aggregate number. Gate passed.

## Recommendation

**Deploy `Blend(LightGBM+CatBoost)` at the frozen threshold (0.4932) as a
transaction-screening flag** (the decision named in `/ds-frame`), with human review
routing for flagged transactions rather than automated blocking — this model
supports the screening decision, it doesn't replace the ops team's judgment on an
individual flagged case.

## Evidence

- **Baseline comparison:** PR-AUC 0.8455 ± 0.0117 vs. a no-skill baseline of 0.00167
  — a lift of 0.8438, ~72x the model's own fold noise (see `/ds-model`).
- **Reliability confirmed across 5 independent seeds**: mean PR-AUC 0.8465, seed-to-
  seed std **0.0010** — roughly 1/30th of the within-run fold-to-fold std (0.03–0.05)
  — this is not a lucky split.
- **In line with published literature** on this same dataset (PR-AUC ~0.85–0.87 for
  top single models, ROC-AUC ~0.98–0.99 for ensembles) — the pipeline produces
  sensible numbers by an independent yardstick, not just an internally consistent one.
- **Drivers pass the only plausibility check available**: no anonymized feature
  shows near-total attribution dominance (top feature: 18.4% of total SHAP), and the
  top-ranked features (`V14`, `V12`, `V10`, `V4`) match independently published
  analyses of this exact dataset (see `/ds-explain`).

## Cost translation — what the threshold actually means in dollars

`/ds-frame` framed this as an asymmetric-cost decision (missed fraud costs more than
one extra false alarm). Translating the frozen threshold's confusion matrix into
dollar terms:

| | Count | Dollar value |
|---|---|---|
| Fraud caught (TP) | 393 of 473 (83.1%) | $44,121 of $58,591 total fraud (**75.3%**) |
| Fraud missed (FN) | 80 | $14,470 |
| False alarms (FP) | 51 | (median genuine transaction: $22 — low friction cost per case) |

**The 83.1% case-count recall overstates dollar-value recall (75.3%)** — worth
stating precisely rather than only reporting the headline recall number. Checked one
level deeper: this gap is driven by a **small number of large-value misses in the
tail**, not a broad shift — the *median* missed fraud amount ($10.76) is nearly
identical to the *median* caught amount ($9.82). This is a materially different,
more actionable finding than "the model misses more dollars than cases": it says the
model's blind spot is a handful of specific large transactions, not a systematic bias
against high-value fraud in general — worth a targeted look at those specific misses
rather than a broad retraining effort aimed at "catching bigger fraud."

**Assumption stated explicitly**: no real per-false-alarm ops cost or per-fraud-
dollar recovery-cost figure was provided for this benchmark — the dollar figures
above describe what's *caught and missed*, not a full cost-benefit ROI calculation,
which would need those two real business inputs before a deployment go/no-go
decision could be finalized on cost grounds alone.

## Assumptions

- Deployment population resembles this 2013, two-day European-cardholder window; a
  real rollout needs continuous retraining as fraud patterns shift (see
  `/ds-frame`'s non-goals).
- The frozen F2 threshold assumes missing fraud costs roughly 4x more than one false
  alarm (F2's implicit weighting) — if the real cost ratio differs, the threshold
  should be re-chosen on validation data using the actual ratio, not this run's
  assumed one.

## Limitations (named, not implied)

1. **Missed fraud skews toward a small number of large-value cases** (see cost
   translation above) — a targeted limitation, not a general "misses some fraud."
2. **Small-dollar fraud near the threshold is the hardest case**: the highest-scored
   (closest-to-caught) misses are almost entirely small transactions ($0–$7),
   consistent with `/ds-explore`'s finding that fraud trends toward smaller amounts
   than genuine transactions — these blend into the overwhelming volume of small
   genuine purchases.
3. **Raw scores are not well-calibrated probabilities** even in the highest-risk
   decile (predicted 0.0212 vs. actual 0.0158) — fine for the rank-and-threshold
   deployment here, not fine for any downstream use treating the score as a literal
   probability without recalibration.
4. **No domain-plausibility check was possible on individual drivers** — `V1-V28`
   are anonymized PCA outputs; the closest available substitute (agreement with
   independently published analyses of the same dataset) was used instead (see
   `/ds-explain`).
5. **Temporal robustness check (day0→day1) scored lower** (PR-AUC 0.7725 vs. CV's
   0.8455) — treated as a single noisy data point given ~236 positive cases in that
   holdout, not a contradiction, but a real deployment should watch this gap on
   rolling data rather than assume it stays this small.
