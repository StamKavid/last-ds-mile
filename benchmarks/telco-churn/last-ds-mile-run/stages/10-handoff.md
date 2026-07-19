# 10 — Reproducibility & Handoff

**Gate check:** environment pinned with exact versions (below) — confirmed.

**Model card:**
- **Predicts:** probability that `Churn = Yes` for an active telecom subscription
  account, given its service/billing/contract profile.
- **Training data:** 5,634 accounts (dev split; 1,409 held out, untouched until
  `/ds-open`), IBM's public Telco Customer Churn sample, 19 features
  (`03-prep.md`).
- **Metric and baseline lift:** AUC = 0.8471 sealed vs. 0.7420 per-`Contract`-type
  churn-rate heuristic baseline — lift = 11.68σ, paired against that baseline
  (`09-report.md`/`04-baseline.md`). Revised from an earlier 27.3σ-vs-constant-0.5
  figure once `sealed_bet` gained a real heuristic-baseline and paired-σ mechanism (see
  `BENCHMARKS.md`); the sealed AUC itself also moved (0.8268 → 0.8471) once a
  stratified-split fix landed and changed the actual dev/held row membership — a real
  data change, not just a math correction (see `06-model.md`).
- **Intended use:** ranking active accounts for proactive retention outreach, checking
  within-segment performance before setting cutoffs rather than assuming uniform
  performance across contract types (`09-report.md`'s recommendation — note the specific
  claim about *which* segment needs the most scrutiny did not hold up across re-seals).
- **Out-of-scope use:** lifetime-value-weighted prioritization (not modeled here); any
  population meaningfully different from this snapshot's pricing/contract structure.

**Environment (pinned, exact versions):**
```
pandas==2.3.3
numpy==2.3.5
scikit-learn==1.7.2
autogluon.tabular==1.5.0
```

**Rerun confirmation:** `/ds-seal` → `/ds-auto` (6 iterations, 1 accepted) → `/ds-open`
reruns cleanly from `prepared.csv` using only the pinned environment above. **Caveat
found by actually re-running this benchmark three times, not just claimed:**
`sealed_bet.auto`'s `_fit_predictor` does not thread a seed into AutoGluon's own internal
model search (documented in its own source comment — `TabularPredictor` exposes no
top-level seed), so a rerun can in principle land on a different winning model even with
the same Contract `seed` — and separately, this benchmark's `strategy="random"` split is
now automatically stratified by `Churn` (a deliberate fix, not an accident — see
`05-validate.md`), which changes *which rows* land in dev vs. held between a pre-fix and
post-fix seal. Concretely: sealed AUC went 0.8268 → 0.8268 → 0.8471 across three re-seals
— identical while only the verdict math changed, then a real shift once the split itself
changed. This stage's "reruns cleanly" claim means "produces an equivalent, similarly-
scoring model from the same inputs," not a bit-for-bit reproducibility guarantee, and a
deliberate mechanism fix (like the stratification one) is expected to move the numbers
for a good reason.

**Artifact location:** refit predictor at `last-ds-mile-run/auto/refit/` (not
committed — regenerable); `Contract`/`LEDGER.md` (the durable, committed evidence) at
`last-ds-mile-run/contract.json` / `last-ds-mile-run/LEDGER.md`.
