# 10 — Handoff

## Reproducibility
- Data: `creditcard.csv` (284,807 rows, unmodified from input).
- Full pipeline (dedup, temporal split, scaling, baseline, all 3 models, threshold
  sweep, subgroup analysis, feature importances): `model_pipeline.py`, deterministic
  (`random_state=42` everywhere it applies).
- Environment: Python 3.14.2, pandas 3.0.3, scikit-learn 1.8.0 (versions as installed
  in this environment — not pinned to a requirements.txt/lockfile, since this was an
  ad hoc analysis, not a packaged deliverable. If this needs to run elsewhere,
  pin these exact versions first.)

## What's NOT handed off
- No serialized model artifact (`.pkl`/`.joblib`) was saved — re-run
  `model_pipeline.py` to regenerate it; not saved by default since no deployment
  target was specified (`00-frame.md`).
- No monitoring/retraining plan — out of scope without a defined deployment decision.

## Open decision for whoever owns this next
The precision/recall operating threshold (see `07-evaluate.md`) was deliberately
left unset — it requires a real cost figure (cost of a missed fraud vs. cost of a
false alarm) that wasn't available this session. Don't ship a threshold without
that input.
