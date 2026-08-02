# 07½ — Iterate Log

## Loop 1

**Diagnosis** (from `.last-ds-mile/stages/07-evaluate.md`'s slice table): the
`Amount: $1-20` slice scores 0.628 PR-AUC vs. 0.792 overall, with 20 fraud
cases in that slice — enough to trust the gap isn't pure fold noise. This
matches the "one or two slices much worse than aggregate" diagnosis →
**slice-specific weakness**, routed back to `/ds-prep`.

**Fix attempted**: added `Amount_rank_pct` (empirical percentile rank of
`Amount` across the dataset — a deterministic, known-at-prediction-time
row-wise transform, same leakage-safety class as `Amount_log`), on the
hypothesis that giving the model an explicit sense of "how small is this
amount relative to the whole distribution" would help it separate small
genuine spend from small fraud better than raw `Amount`/`log1p(Amount)`
alone.

**Result**: no improvement.

| | Without `Amount_rank_pct` | With `Amount_rank_pct` |
|---|---|---|
| CV val PR-AUC (train, 5-fold) | 0.860 ± 0.031 | 0.859 ± 0.031 |
| Test PR-AUC (held-out) | 0.792 | 0.782 |
| Amount $1-20 slice PR-AUC (test) | 0.628 | 0.608 |

The added feature moved nothing meaningfully, and the targeted slice got
marginally worse, not better — the XGBoost model already had access to
`Amount` directly and evidently wasn't missing a "relative size" signal;
the weakness is more likely that small-amount fraud and small-amount
genuine transactions are genuinely harder to separate on the PCA feature
set available, not a missing-feature problem this fix could address.

**Decision**: stop iterating on this diagnosis. One well-motivated,
specific fix was tried and didn't move the number — per `ds-iterate`'s
cap-iteration guidance, looping further on the same slice without a new
hypothesis would be noise-chasing, not iteration. Keeping the original
model (without `Amount_rank_pct`) as final, since it's marginally better
and simpler.

**Verdict: proceed to `/ds-explain`.** The `Amount: $1-20` slice weakness
(PR-AUC 0.628 vs. 0.792 overall) is carried forward as a **stated,
unresolved limitation** for `/ds-report` — not silently dropped. No other
diagnosis from `/ds-evaluate` (calibration, the CV-vs-test gap, the other
low-fraud-count slices) rose to the level of a specific, actionable fix
within this evidence; the CV-vs-test gap in particular was already
assessed in `/ds-evaluate` as plausibly sampling noise given only 74 test
fraud cases, and doesn't have a distinct fix beyond what `/ds-validate`
already chose (chronological split) to guard against it.
