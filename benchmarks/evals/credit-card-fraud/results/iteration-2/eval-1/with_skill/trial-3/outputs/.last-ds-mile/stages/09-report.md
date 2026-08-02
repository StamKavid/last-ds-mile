# 09 — Report

## What was built

An XGBoost classifier detecting fraudulent transactions in `creditcard.csv`
(284,807 transactions, 0.17% fraud). Full pipeline: framing → data
understanding → EDA → cleaning/features → baseline → validation design →
modeling → evaluation → iteration, artifacts in `.last-ds-mile/stages/`.

## How well it works

- **Primary metric: PR-AUC (average precision) = 0.792** on a held-out
  chronological test set (last 20% of transactions by time, never touched
  during training/tuning) — a **474x lift** over the majority-class
  baseline (0.00167).
- At a frozen operating threshold (0.681, chosen before touching the test
  set): **75.7% recall, 88.9% precision** — catches 56 of 74 fraud cases,
  flags only 7 genuine transactions out of 56,672 as false alarms.
- Reasonably well calibrated in the top probability decile (predicted 1.4%
  vs. observed 1.3% fraud rate), where the operating threshold sits.

## Known limitations (stated explicitly, not glossed over)

1. **No confirmed deployment context.** The cost tradeoff between missing
   fraud vs. false alarms was never answered (asked, no response) — the
   0.681 threshold is F1-optimizing, not cost-calibrated. Before
   production use, get the real cost numbers and re-pick the threshold.
2. **Weaker on small transactions**: PR-AUC 0.628 for $1–20 transactions
   vs. 0.792 overall — tried one specific fix (a relative-amount feature),
   it didn't help; this is a genuine, unresolved gap in the current
   feature set (see `07-iterate-log.md`).
3. **CV (0.860) overstated the held-out result (0.792)** by more than the
   CV fold spread — flagged as likely partial optimism from the validation
   design's compromise (stratified-random inner CV vs. the truly
   chronological outer test), partly small-sample noise (only 74 fraud
   cases in test). Report the 0.792 test number, not the 0.860 CV number.
4. Dataset is 2013, fully anonymized (PCA features, no interpretable raw
   attributes) — no root-cause story for *why* specific transactions are
   flagged is possible beyond amount/time.

## Next steps if this moves toward production

- Get an actual cost-of-fraud vs. cost-of-false-alarm number and re-freeze
  the threshold against it.
- More recent, less-anonymized data would let calibration and slice
  analysis be far more actionable (e.g. merchant category, device signals).
- `/ds-handoff` (pinned environment, reproducibility) not yet run — do
  this before treating `final_model.joblib` as anything beyond an
  analysis artifact.
