# 09 — Report

**Gate check:** `07-evaluate.md` includes slice performance (by `Contract` type), not
only an aggregate number — confirmed before writing.

**Decision this informs** (from `00-frame.md`): which customers a retention team should
proactively target with a save offer before their next billing cycle.

**Recommendation:** use the model's predicted churn probability to rank and target
customers for outreach, prioritizing the highest-scoring accounts within each contract
segment separately rather than one global cutoff — since `07-evaluate.md` shows the
model's discriminative power varies meaningfully by contract type (AUC 0.68–0.76
within-slice vs. 0.83 overall), a single global threshold would implicitly
over-prioritize month-to-month/two-year customers (where the model's job is
easier) at the expense of one-year customers (where it's hardest but the churn rate,
15.3%, is still real money).

**Evidence:**
- **Baseline comparison:** sealed AUC 0.827 vs. 0.5 baseline (a constant-probability
  prediction), lift = 27.3σ — decisively real.
- **Calibration:** genuinely usable as an approximate real probability, not just a rank
  (see `07-evaluate.md`'s decile table) — useful if the retention team wants to budget
  outreach by expected-value, not just rank order.
- **Ceiling context:** sealed AUC (0.827) sits a bit below the human ceiling estimate
  (0.85, informed by the wider Kaggle/community consensus range of ~0.82–0.86 for this
  dataset) — a solid, credible result within the range this problem is generally
  understood to top out around, not an outlier in either direction.

**Assumptions and limitations:**
- The overall AUC is partly driven by an "easy" macro-signal (`Contract` type) — see
  `07-evaluate.md`'s slice table before assuming uniform performance across segments.
- `roc_auc` was used because it's what `sealed_bet` currently supports; for a
  retention-targeting decision specifically, **AUPRC (precision-recall) would arguably
  be the more decision-relevant metric** — the team ultimately cares about how many of
  the accounts it spends outreach budget on are genuine churners, which precision-recall
  captures more directly than ROC-AUC does under a 26.5% positive rate. Noted as a real,
  current gap (see `BENCHMARKS.md`), not resolved in this run.
- No lifetime-value weighting — this ranks by churn probability alone, not by
  probability × the revenue at stake per account.
