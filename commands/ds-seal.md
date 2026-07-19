---
description: Seal a holdout and write the Contract — the one human signature of the Sealed Bet
---

Seal the dataset so the rest of the work is honest by construction.

1. Confirm with the user: the target column, the task (regression/classification),
   the metric, and the split strategy (`random`, or `group`/`time` with a key/column).
   If a column repeats per entity, recommend `group`; if there is a date and the
   prediction is forward-looking, recommend `time`. (Full auto-recommendation lands
   in a later release; for now confirm these explicitly.) Also ask: "do you have a
   domain benchmark or expert-performance number for this problem?" — if yes, that
   becomes the ceiling estimate; if no, `seal.py` computes one automatically (an
   approximation, not a true domain ceiling). If `--time-col` is a raw timestamp
   with no standalone predictive legitimacy (unlike e.g. a derived "current
   calendar month" feature, which can legitimately stay in the model), pass it to
   `--exclude-from-features` too — it's still used to build the split, but never
   reaches the model's own inputs. For an imbalanced classification target with
   `--strategy random`, stratification by the target is automatic — no flag needed.
2. Check `.last-ds-mile/stages/04-baseline.md` for a real non-ML heuristic (a
   business rule, a lookup) — not just the dumb constant `/ds-baseline` always
   scores. If one exists, write it as a small Python module with a function
   `(dev_df, held_features_df) -> predictions` (one prediction per held row,
   in `held_features_df`'s row order) and pass
   `--baseline-py path/to/file.py:function_name`. Without this, the Contract's
   `baseline_score` is a constant prediction — for `roc_auc` that scores
   exactly 0.5 on every dataset by construction, a floor rather than a rival,
   and every ship-gate lift is measured against that floor, not against
   "better than what a human would actually do instead."
3. Run:
   `python -m sealed_bet.seal --data <path> --target <col> --task <task> --metric <metric> --strategy <strategy> [--group-key <col>] [--time-col <col>] [--ceiling-estimate <number, if the user gave one>] [--baseline-py <path:function, if step 2 found one>] [--exclude-from-features <comma-separated columns, if any>]`
4. Tell the user the seal is set: they may now build freely on `.last-ds-mile/dev.csv`
   (or run `/ds-auto` to build autonomously); the holdout labels are locked and
   `seal_guard` will refuse to read them. When ready, `/ds-open` settles the bet —
   once.
