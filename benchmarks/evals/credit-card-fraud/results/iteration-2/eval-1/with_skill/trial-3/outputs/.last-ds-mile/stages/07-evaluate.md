# 07 — Evaluation & Error Analysis

## Aggregate metric (the `/ds-frame` metric, on the frozen held-out chronological test set)

**Test PR-AUC (average precision) = 0.792**, bootstrap 95% CI [0.702, 0.874]
(1,000 resamples of the 56,746-row test set, std 0.045).

This is **below** the CV validation estimate from `/ds-model` (0.860 ± 0.031).
The gap (0.068) exceeds the CV fold spread but sits inside the test-set
bootstrap CI — flagged honestly rather than smoothed over: with only 74
fraud cases in the test set, some of this drop is plausibly sampling noise,
but it is also consistent with `/ds-validate`'s documented compromise (CV
folds were stratified-random within the training window, not
forward-chained) producing a mildly optimistic validation number. **The
number to trust for "how well does this work" is 0.792 (test), not 0.860
(CV)** — CV was for model selection, this is the honest estimate.

For context: baseline PR-AUC was 0.00167 (`/ds-baseline`) — a **474x** lift.

## Hard-threshold performance (frozen threshold = 0.681, chosen in `/ds-model` before seeing this test set)

| | Predicted genuine | Predicted fraud |
|---|---|---|
| **Actual genuine** | 56,665 (TN) | 7 (FP) |
| **Actual fraud** | 18 (FN) | 56 (TP) |

- Precision: 0.889 (89% of flagged transactions are actually fraud)
- Recall: 0.757 (catches 56 of 74 fraud cases; misses 18)
- F1: 0.818

## Calibration

Predicted-probability deciles vs. observed fraud rate (full table in
`model_evaluate.py` output; `.last-ds-mile/figures/07-calibration.png`):
the top decile (predicted prob 0.0002–1.0) has mean predicted probability
1.4% vs. observed rate 1.3% — reasonably well calibrated at the top end,
where the operating threshold actually sits. Lower deciles are all
correctly near-zero on both axes (no systematic over/under-confidence
observed at the low end either).

## Slice performance

No protected/sensitive attributes exist in this dataset (fully anonymized
PCA features, no age/gender/geography/etc.) — confirmed, so no
protected-attribute slicing applies. Sliced instead by the two
business-meaningful dimensions available: transaction amount and
time-of-day within the window.

| Slice | n | n_fraud | PR-AUC |
|---|---|---|---|
| Overall | 56,746 | 74 | **0.792** |
| Amount: $0–1 | 6,371 | 28 | 0.909 |
| Amount: $1–20 | 23,623 | 20 | 0.628 |
| Amount: $20–100 | 16,860 | 11 | 0.910 |
| Amount: $100–1000 | 9,390 | 13 | 0.741 |
| Amount: $1000+ | 502 | 2 | 0.504 |
| Time-of-day: 12–18h (window) | 22,349 | 40 | 0.857 |
| Time-of-day: 18–24h (window) | 34,397 | 34 | 0.725 |

See `.last-ds-mile/figures/07-slice-performance.png`.

**Findings**:
- **Amount $1–20 is a real weak spot** (PR-AUC 0.628 vs 0.792 overall, 20
  fraud cases — enough to trust the gap isn't pure noise). Small-value fraud
  is harder to distinguish from small-value genuine spend.
- **Amount $1000+ (0.504) and Time-of-day 18-24h being lower are noted but
  not trusted as strong findings** — the $1000+ slice has only 2 fraud
  cases, too few for a stable PR-AUC estimate; flagged as low-confidence,
  not a conclusion.
- **Time-of-day coverage is limited by construction**: because the test
  set is only the chronological last 20% of a 48-hour window, its
  `Time`-of-day values only span ~16h–24h of the cycle — the 0–6h and
  6–12h buckets have zero test rows. This is a structural artifact of the
  validation design (`/ds-validate`), not a modeling finding; time-of-day
  slicing here is directional at best.

## Error analysis

**18 false negatives** (missed fraud): predicted probabilities are all very
low (0.00006–0.03), i.e. the model isn't "almost catching" these — it's
confidently wrong. Amounts span a wide range ($0–$1,097) with no obvious
shared pattern visible in `Amount`/`Time` alone (the PCA features that
likely explain them aren't human-interpretable, per `/ds-data`). Hypothesis:
these are fraud cases that look statistically like ordinary transactions on
the available features — a harder subclass of fraud this feature set
doesn't capture, not a bug.

**7 false positives**: five have very small amounts (four at $0.77, one at
$2.00), one is $451.81, and one is the test set's largest transaction,
**$25,691.16 — the single largest amount in the entire dataset** — flagged
as fraud with 93% confidence but is actually genuine. Hypothesis: the model
has learned "unusually large or unusually small amount" as a fraud signal
(consistent with the `Amount==0` fraud-rate finding in `/ds-explore`), which
correctly flags most real fraud but also catches legitimate extreme-value
transactions. This is the expected precision/recall tradeoff, not an error
worth "fixing" without a cost function to rebalance against.

## Distribution shift

Already checked in `/ds-validate` (train vs. test fraud rate: 0.176% vs
0.130%, a modest but not alarming drop). No new deployment population
exists beyond this dataset to check further.

## Figures exported

- `.last-ds-mile/figures/07-calibration.png`
- `.last-ds-mile/figures/07-slice-performance.png`
