import numpy as np
import pandas as pd

from sealed_bet.auto import diagnose, ladder_accept, run_iteration, ceiling_baseline, EARLY_STOP_AFTER


def _run_build_loop(dev, target, feature_cols_by_iter, task, metric, ceiling_score,
                    budget, seed, time_limit, model_dir_root):
    """A scaled-down version of what the /ds-auto command's own loop does,
    used here only to prove the primitives compose correctly end to end.
    feature_cols_by_iter: a list of feature_cols lists, one to try per
    iteration (stands in for the command's own per-iteration framing choice).
    """
    from sealed_bet.metrics import METRICS
    m = METRICS[metric]
    best_score = None
    best_train_score = None
    consecutive_rejections = 0
    history = []

    for i, feature_cols in enumerate(feature_cols_by_iter[:budget], start=1):
        result = run_iteration(
            dev_df=dev, target=target, feature_cols=feature_cols, task=task,
            metric=metric, seed=seed, time_limit=time_limit,
            model_dir=f"{model_dir_root}/iter{i}",
        )
        if best_score is None:
            accepted = True
        else:
            accepted = ladder_accept(result["dev_score"], best_score, result["noise_floor"],
                                     m.greater_is_better)
        if accepted:
            best_score = result["dev_score"]
            best_train_score = result["train_score"]
            consecutive_rejections = 0
        else:
            consecutive_rejections += 1
        regime = diagnose(result["train_score"], result["dev_score"], result["noise_floor"],
                          ceiling_score, m.greater_is_better)["regime"]
        history.append({"iter": i, "regime": regime, "accepted": accepted,
                        "dev_score": result["dev_score"]})
        if consecutive_rejections >= EARLY_STOP_AFTER:
            break
    return {"best_score": best_score, "history": history}


def test_build_loop_converges_toward_the_ceiling_on_a_genuinely_learnable_problem(tmp_path):
    # Iteration 1 gets only a noise feature; iteration 2+ get the real signal.
    # A working loop should show the 2nd (and later) iteration's dev_score
    # clearing the Ladder over iteration 1's, proving the loop can actually
    # improve when a better framing becomes available.
    rng = np.random.default_rng(0)
    n = 300
    dev = pd.DataFrame({
        "noise": rng.normal(size=n),
        "signal": rng.normal(size=n),
    })
    dev["y"] = (dev["signal"] > 0).astype(int)

    ceiling = ceiling_baseline(dev, "y", ["signal"], "classification", "roc_auc",
                               seed=0, time_limit=15, model_dir=str(tmp_path / "ceiling"))

    result = _run_build_loop(
        dev, target="y",
        feature_cols_by_iter=[["noise"], ["signal"], ["signal"], ["signal"]],
        task="classification", metric="roc_auc", ceiling_score=ceiling["score"],
        budget=4, seed=0, time_limit=15, model_dir_root=str(tmp_path / "loop1"),
    )
    # iteration 1 (noise-only) should score near chance; a later iteration
    # using the real "signal" feature should be accepted as a clear improvement
    assert result["history"][0]["dev_score"] < 0.65
    accepted_iters = [h for h in result["history"] if h["accepted"]]
    assert len(accepted_iters) >= 2  # iter 1 (baseline-best) + at least one real improvement
    assert result["best_score"] > 0.75


def test_build_loop_early_stops_when_every_framing_is_genuine_noise(tmp_path):
    # every iteration gets an unrelated random feature -- none should ever
    # meaningfully beat the first iteration's score, so the Ladder should
    # reject enough in a row to trigger early-stop well before the budget
    # (6 iterations here) is exhausted.
    rng = np.random.default_rng(1)
    n = 300
    dev = pd.DataFrame({f"noise{i}": rng.normal(size=n) for i in range(8)})
    dev["y"] = rng.integers(0, 2, size=n)  # target independent of every feature

    ceiling = ceiling_baseline(dev, "y", ["noise0"], "classification", "roc_auc",
                              seed=1, time_limit=15, model_dir=str(tmp_path / "ceiling2"))

    feature_cols_by_iter = [[f"noise{i}"] for i in range(8)]
    result = _run_build_loop(
        dev, target="y", feature_cols_by_iter=feature_cols_by_iter,
        task="classification", metric="roc_auc", ceiling_score=ceiling["score"],
        budget=8, seed=1, time_limit=12, model_dir_root=str(tmp_path / "loop2"),
    )
    # early-stop must have kicked in before exhausting the full budget of 8
    assert len(result["history"]) < 8
    rejected_tail = [h["accepted"] for h in result["history"][-EARLY_STOP_AFTER:]]
    assert not any(rejected_tail)  # the last EARLY_STOP_AFTER were all rejections
