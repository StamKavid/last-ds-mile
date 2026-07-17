# 10 — Reproducibility & Handoff

**Gate check:** environment pinned with exact versions (below) — confirmed.

**Model card:**
- **Predicts:** probability that `Churn = Yes` for an active telecom subscription
  account, given its service/billing/contract profile.
- **Training data:** 5,634 accounts (dev split; 1,409 held out, untouched until
  `/ds-open`), IBM's public Telco Customer Churn sample, 19 features
  (`03-prep.md`).
- **Metric and baseline lift:** AUC = 0.827 sealed vs. 0.5 baseline — lift = 27.3σ
  (`09-report.md`).
- **Intended use:** ranking active accounts for proactive retention outreach,
  ideally within contract-type segments (`09-report.md`'s recommendation).
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
reruns cleanly from `prepared.csv` using only the pinned environment above.

**Artifact location:** refit predictor at `last-ds-mile-run/auto/refit/` (not
committed — regenerable); `Contract`/`LEDGER.md` (the durable, committed evidence) at
`last-ds-mile-run/contract.json` / `last-ds-mile-run/LEDGER.md`.
