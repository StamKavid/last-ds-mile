# 06 — Modeling

**Gate check:** `04-baseline.md` and `05-validate.md` both exist and were read before
modeling began — confirmed.

Modeling done through the Sealed Bet mechanism (`/ds-seal` → `/ds-auto` → `/ds-open`);
the full experiments table lives in `.last-ds-mile-run/LEDGER.md`'s `## Build (auto)`
section.

**Summary:** iteration 1 (all 19 features) won. Five subsequent attempts to resolve the
`high_variance` regime (dropping weak categoricals, engineering a `tenure_bucket`
feature) were all rejected by the Ladder as within the noise floor — the same pattern
seen in the House Prices case (`../house-prices/`): `diagnose()`'s train-vs-val gap for
this AutoGluon ensemble didn't meaningfully shrink from modest feature changes, and the
loop correctly early-stopped after 5 consecutive rejections. Refit on full dev, scored
on the sealed held set: **AUC = 0.827, lift = 27.3σ over the 0.5 baseline** — see
`09-report.md` and `BENCHMARKS.md`.
