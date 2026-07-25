# 7½ — Iterate

## Diagnosis of `07-evaluate.md` findings
- Large, real lift over baseline (PR-AUC 0.814 vs 0.0013) — not a leakage artifact
  (CV-vs-holdout gap is small and explained by a known distribution shift, not by a
  broken split).
- One real weakness found: recall drops to ~36% in the $5–$20 transaction bucket
  vs ~70% elsewhere. Sample size in that bucket (11 fraud) is small enough that this
  could partially be noise, but it repeats the same direction consistently.
- No leakage red flags, no validation-beats-training anomaly, no single feature
  suspiciously dominating importance.

## Route decision
**Proceed** — not routing back to `/ds-prep`, `/ds-validate`, or `/ds-model`.

Reasoning: the $5-$20 subgroup weakness is worth reporting honestly (see
`07-evaluate.md`), but with only 11 fraud cases in that bucket, further tuning
specifically targeted at it risks overfitting to noise rather than fixing a real
pattern. It's flagged for the user in the final report as a known limitation rather
than chased with more modeling on this pass. The open threshold decision (recall
70% @ 99% precision vs. recall 80%+ @ ~50% precision) is a business decision, not a
modeling gap — nothing left to iterate on without that input.

**Verdict: proceed to `/ds-explain` and `/ds-report`.**
