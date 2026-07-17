---
description: Run the autonomous Build loop between /ds-seal and /ds-open — diagnose, frame, delegate to AutoGluon, Ladder-accept, repeat
---

Run the Build loop against the sealed Contract. This runs autonomously within
this turn, up to the Contract's `budget` or 5 consecutive Ladder rejections —
no mid-loop check-ins, but every iteration is logged to `LEDGER.md` (same
path convention as `/ds-seal`/`/ds-open`) as it happens so it stays watchable.

1. Load `.last-ds-mile/contract.json` (via `sealed_bet.contract.Contract.load`)
   for `target`, `task`, `metric`, `budget`, `ceiling_score`, `ceiling_source`,
   and the split `strategy`/`group_key`/`time_col`. Load `.last-ds-mile/dev.csv`
   into `dev_df`.
2. Track across iterations: the loop counter `i` (starts at 1), `best_score`,
   `best_train_score`, `best_feature_cols` (starts as all `dev_df` columns
   except the target), `noise_floor` (from the most recent iteration), and
   `consecutive_rejections = 0`.
3. Repeat, up to `budget` times or until `consecutive_rejections >= 5`:
   a. On iteration 1, skip diagnosis — regime is `"baseline"` and this
      iteration is unconditionally accepted (see step d). Run it on the full
      feature set to establish where things stand. On iteration 2+, call
      `sealed_bet.auto.diagnose(best_train_score, best_score, noise_floor,
      ceiling_score, greater_is_better)` (using the previous iteration's
      `noise_floor` and the metric's `greater_is_better` from
      `sealed_bet.metrics.METRICS`) to get the regime for this iteration.
   b. Based on the regime, decide ONE concrete change to `feature_cols` for
      this iteration, then state it in one short sentence — this becomes the
      Ledger's `framing_note`:
      - `high_variance` → drop one or more features from `best_feature_cols`.
        (Regularization or model-family changes are AutoGluon's job, not
        something to hand-tune here — dropping features is the one lever
        this loop pulls for this regime.)
      - `high_bias` → engineer a new feature (e.g. an interaction or
        derived column) into a working copy of `dev_df`, then add its name
        to `feature_cols`.
      - `neither` → engineer a new framing of an existing feature (a
        transform or encoding, not just more of the same) into `dev_df` the
        same way, and swap it in for the feature it replaces.
      Never adjust hyperparameters or model family directly — that's
      `run_iteration`'s (AutoGluon's) job entirely.
   c. Call `sealed_bet.auto.run_iteration(dev_df, target, feature_cols, task,
      metric, strategy=strategy, group_key=group_key, time_col=time_col,
      seed=0, model_dir=f".last-ds-mile/auto/iter{i}")` — always pass an
      explicit `model_dir` under `.last-ds-mile/auto/` so AutoGluon never
      writes to the repo root. Update `noise_floor` from this result.
   d. On iteration 1: set `best_score`/`best_train_score`/`best_feature_cols`
      unconditionally from this result, and treat it as accepted. On
      iteration 2+: call `sealed_bet.auto.ladder_accept(new_score, best_score,
      noise_floor, greater_is_better)`; if `True`, update all three `best_*`
      and reset `consecutive_rejections` to 0; if `False`, increment
      `consecutive_rejections` and leave `best_*` unchanged.
   e. Call `sealed_bet.ledger.append_build_iteration("LEDGER.md", i, regime,
      framing_note, dev_score, accepted)` every iteration, accepted or not
      (iteration 1 logs `regime="baseline"`, `accepted=True`). Increment `i`.
4. Once the loop ends, call `sealed_bet.auto.refit_winner(dev_df, target,
   best_feature_cols, task, seed=0, model_dir=".last-ds-mile/auto/refit")` to
   refit the winning framing on the full dev set (not just its outer-train
   fold from whichever iteration won).
5. Generate predictions for `.last-ds-mile/held/features.csv`, subset to
   `best_feature_cols` (same convention as `run_iteration`'s own internal
   scoring), using the refit predictor (`predict_proba(...)[1]` for
   classification, `predict(...)` for regression). Write them as a
   single-column CSV to `preds.csv`.
6. Report a summary: how many iterations ran, how many were accepted, the
   best dev score, the ceiling score and its source, and that `preds.csv` is
   ready. Tell the user `/ds-open` settles the bet next.
