---
description: Run the autonomous Build loop between /ds-seal and /ds-open — diagnose, frame, delegate to AutoGluon, Ladder-accept, repeat
---

Run the Build loop against the sealed Contract. This runs autonomously within
this turn, up to the Contract's `budget` or 5 consecutive Ladder rejections —
no mid-loop check-ins, but every iteration is logged to `LEDGER.md` as it
happens so it stays watchable.

1. Load `.last-ds-mile/contract.json` (via `sealed_bet.contract.Contract.load`)
   for `target`, `task`, `metric`, `budget`, `ceiling_score`, and the split
   `strategy`/`group_key`/`time_col`. Load `.last-ds-mile/dev.csv`.
2. Track `best_score`, `best_train_score`, `best_feature_cols` (starts as all
   dev columns except the target), and `consecutive_rejections = 0`.
3. Repeat, up to `budget` times or until `consecutive_rejections >= 5`:
   a. If this is iteration 1, skip diagnosis — run the first iteration on the
      full feature set to establish a baseline. Otherwise, call
      `sealed_bet.auto.diagnose(best_train_score, best_score, noise_floor,
      ceiling_score, greater_is_better)` (use the last iteration's
      `noise_floor` and the metric's `greater_is_better` from
      `sealed_bet.metrics.METRICS`) to get the regime.
   b. Based on the regime, decide ONE concrete change to try this iteration:
      `high_variance` → drop features, or note that regularization/data
      constraints are AutoGluon's job, not something to hand-tune;
      `high_bias` → add a feature or interaction; `neither` → try a new
      feature framing (a transform, an encoding) rather than more capacity.
      State the framing in one short sentence — this becomes the Ledger's
      `framing_note`. Never adjust hyperparameters or model family directly —
      that's `run_iteration`'s (AutoGluon's) job entirely.
   c. Call `sealed_bet.auto.run_iteration(dev_df, target, feature_cols, task,
      metric, strategy=strategy, group_key=group_key, time_col=time_col,
      seed=0, model_dir=f".last-ds-mile/auto/iter{i}")` — always pass an
      explicit `model_dir` under `.last-ds-mile/auto/` so AutoGluon never
      writes to the repo root.
   d. On iteration 1, `best_score`/`best_train_score`/`best_feature_cols` are
      set unconditionally from this iteration's result. On later iterations,
      call `sealed_bet.auto.ladder_accept(new_score, best_score, noise_floor,
      greater_is_better)`; if `True`, update all three `best_*` and reset
      `consecutive_rejections` to 0; if `False`, increment
      `consecutive_rejections` and leave `best_*` unchanged.
   e. Call `sealed_bet.ledger.append_build_iteration(ledger_path, i, regime,
      framing_note, dev_score, accepted)` every iteration, accepted or not.
4. Once the loop ends, call `sealed_bet.auto.refit_winner(dev_df, target,
   best_feature_cols, task, seed=0, model_dir=".last-ds-mile/auto/refit")` to
   refit the winning framing on the full dev set (not just its outer-train
   fold from whichever iteration won).
5. Generate predictions for `.last-ds-mile/held/features.csv` using the
   refit predictor (`predict_proba(...)[1]` for classification, `predict(...)`
   for regression) and write them as a single-column CSV to `preds.csv`.
6. Report a summary: how many iterations ran, how many were accepted, the
   best dev score, the ceiling score and its source, and that `preds.csv` is
   ready. Tell the user `/ds-open` settles the bet next.
