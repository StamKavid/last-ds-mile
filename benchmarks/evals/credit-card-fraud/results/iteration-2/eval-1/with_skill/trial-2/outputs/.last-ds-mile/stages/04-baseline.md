# 04 — Honest Baseline

## Baseline definition
Majority-class classifier: predict "genuine" (0) for every transaction. This is the
correct dumb baseline here — there's no simpler rule in informal use, and no
strong temporal/seasonal structure to build a stronger simple anchor from (per
`00-frame.md`'s "do we need ML" check, a single-field rule like an amount threshold
was already checked and rejected in `02-explore.md`).

Evaluated on the exact temporal test split defined in `05-validate.md` (last 30% by
`Time`, 85,118 rows, 107 fraud).

## Baseline score (using the exact metrics from `00-frame.md`)
- **Accuracy: 99.874%** — meaningless here; stated explicitly to preempt anyone
  reading it as evidence of a good model (this is exactly the imbalance trap
  `00-frame.md` flagged).
- **PR-AUC (average precision): 0.00126** — equal to test-set fraud prevalence, which
  is the mathematical floor for a no-skill classifier on this metric.
- **ROC-AUC: 0.500** — no-skill line.
- Precision/recall/F1 for the fraud class: all 0 (the classifier never predicts
  positive, so precision is undefined and recall is 0 by construction).

## What "beating it" means
Any real model must clear **PR-AUC ≫ 0.00126** (not just >0, since anything above
the ~0.1% floor is trivially achievable by luck) — a PR-AUC in the 0.7–0.9+ range, as
found in `06-model.md`, represents genuine, large lift, not noise.
