# 09 — Report

**Gate check:** `07-evaluate.md` includes slice performance (by `Contract` type), not
only an aggregate number — confirmed before writing.

**Decision this informs** (from `00-frame.md`): which customers a retention team should
proactively target with a save offer before their next billing cycle.

**Recommendation:** use the model's predicted churn probability to rank and target
customers for outreach. Check within-segment performance before setting cutoffs rather
than assuming the overall 0.8471 AUC applies uniformly — `07-evaluate.md` shows
within-slice AUC (0.75–0.77) meaningfully below the aggregate for every `Contract`
segment, so a single global threshold implicitly over-prioritizes whichever segment the
aggregate number is most flattered by. **Revised from a more specific "prioritize
one-year contracts especially" recommendation:** that tactical claim rested on the
previous re-seal finding one-year contracts the hardest slice, which flipped to easiest
on this re-seal's stratified split (`07-evaluate.md`) — a genuinely unstable result at
this sample size, not something to hang an operational recommendation on. The stable,
re-seal-independent finding is "check per-segment, don't trust the aggregate blindly";
which specific segment needs the most scrutiny should be re-verified against the
production model's own held-out performance, not assumed from this benchmark.

**If the retention offer under consideration involves a contract upgrade specifically**
(e.g. "sign a longer contract, get a discount"): see [`../CAUSAL_ANALYSIS.md`](../CAUSAL_ANALYSIS.md)
for a genuinely different, complementary question this ranking model doesn't answer —
whether a contract upgrade *causes* lower churn (yes, but roughly 14pp on average, not
the 36pp naive correlation, and up to ~34–40pp for new/fiber customers specifically).
This model tells the team *who* is likely to churn; that analysis tells them *which
customers a contract-upgrade intervention would actually help*.

**Evidence:**
- **Baseline comparison (revised — see `04-baseline.md`/`06-model.md`):** sealed AUC
  0.8471 vs. a real, scored non-ML rival — the historical churn rate per `Contract`
  type, AUC 0.7420 — **lift = 11.68σ**, using the paired bootstrap difference between
  the model's and baseline's scores on the same held rows as σ. This is a smaller, more
  honest lift than the 27.3σ this report originally cited: that number was measured
  against a constant 0.5-AUC prediction (a floor that's identical for every
  classification dataset by construction, not specific to this one) using the model's
  own score variance in isolation as σ. Still decisively above the 2σ ship threshold —
  the model is reliably better than "know last quarter's churn rate per segment," not
  just reliably better than a coin flip.
- **Calibration:** genuinely usable as an approximate real probability, not just a rank
  (see `07-evaluate.md`'s decile table) — useful if the retention team wants to budget
  outreach by expected-value, not just rank order. (Freshly recomputed via
  `sealed_bet.score.reveal()`; see that stage's note.)
- **Ceiling context:** sealed AUC (0.8471) sits close to the human ceiling estimate
  (0.85, informed by the wider Kaggle/community consensus range of ~0.82–0.86 for this
  dataset) — a solid, credible result within the range this problem is generally
  understood to top out around, not an outlier in either direction.

**Assumptions and limitations:**
- The overall AUC is partly driven by an "easy" macro-signal (`Contract` type) — see
  `07-evaluate.md`'s slice table before assuming uniform performance across segments.
  Note the sealed model's lift is now measured directly against a `Contract`-rate
  heuristic, so this segment-driven signal is no longer double-counted as "beating the
  baseline" the way it implicitly was when the baseline was a flat constant.
- `roc_auc` was used because it's what `sealed_bet` currently supports; for a
  retention-targeting decision specifically, **AUPRC (precision-recall) would arguably
  be the more decision-relevant metric** — the team ultimately cares about how many of
  the accounts it spends outreach budget on are genuine churners, which precision-recall
  captures more directly than ROC-AUC does under a 26.5% positive rate. Noted as a real,
  current gap (see `BENCHMARKS.md`), not resolved in this run.
- No lifetime-value weighting — this ranks by churn probability alone, not by
  probability × the revenue at stake per account.
- The split-adversary Probe now runs (a categorical-encoding/missing-value bug that
  previously crashed it on every real dataset is fixed — see `BENCHMARKS.md`) and
  reports **CERTIFIED ✅** (train-vs-held AUC 0.5038, lift 0.46σ) — dev and held are
  statistically indistinguishable, as expected for this (now automatically stratified —
  see `05-validate.md`) `random` split. The leakage-adversary Probe (previously dead
  code, never wired into `seal()`) also now runs and reports CLEAR: no feature
  solo-predicts `Churn` above the 0.95 threshold (top: `tenure` at 0.737), consistent
  with `08-explain.md`'s feature-importance sanity check.
- This benchmark was re-sealed three times as `sealed_bet` gained fixes (baseline,
  paired σ, wired-in probes, then stratification). The headline numbers moved each time
  (see `06-model.md`), and one specific finding — which `Contract` slice is hardest —
  flipped entirely between re-seals (`07-evaluate.md`). Treat this benchmark's exact
  numbers as illustrative of the mechanism working correctly, not as a permanent,
  citable score for this dataset; a fresh `/ds-seal` run today would very plausibly land
  on slightly different numbers again, for reasons that have nothing to do with the
  model being wrong.
