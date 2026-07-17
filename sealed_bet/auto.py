"""auto.py: the Build loop's mechanical primitives.

diagnose() classifies the bias/variance regime from a train/val score pair.
run_iteration() delegates one iteration's fit+score to AutoGluon, via an
outer-train/outer-val nested-CV split so AutoGluon's own internal search
never contaminates the score used to judge this iteration.
ladder_accept() is the noise-floor acceptance rule that stops the Build loop
from chasing noise across many iterations against the same dev data.
ceiling_baseline() and refit_winner() are the remaining AutoGluon call sites:
the mandatory ceiling estimate, and the final full-dev refit before scoring
the held set.

All scoring goes through sealed_bet.metrics.METRICS -- never AutoGluon's own
internal evaluation -- so one statistical language runs through the product.
"""
from __future__ import annotations

import tempfile

from autogluon.tabular import TabularPredictor

from sealed_bet.metrics import METRICS, bootstrap_sigma
from sealed_bet.splits import split


EARLY_STOP_AFTER = 5  # consecutive Ladder rejections before the Build loop gives up


def ladder_accept(new_score: float, best_score: float, noise_floor: float,
                  greater_is_better: bool) -> bool:
    delta = (new_score - best_score) if greater_is_better else (best_score - new_score)
    return delta > noise_floor


def diagnose(train_score: float, val_score: float, noise_floor: float,
            ceiling_score: float, greater_is_better: bool) -> dict:
    gap = (train_score - val_score) if greater_is_better else (val_score - train_score)
    gap_to_ceiling = (ceiling_score - val_score) if greater_is_better else (val_score - ceiling_score)
    if gap > noise_floor:
        regime = "high_variance"
    elif gap_to_ceiling > noise_floor:
        regime = "high_bias"
    else:
        regime = "neither"
    return {"regime": regime, "gap": gap}


def _fit_predictor(train_df, target: str, task: str, model_dir: str | None,
                   time_limit: int):
    problem_type = "regression" if task == "regression" else "binary"
    path = model_dir or tempfile.mkdtemp(prefix="sealed_bet_autogluon_")
    return TabularPredictor(
        label=target, problem_type=problem_type, verbosity=0, path=path,
    ).fit(train_df, time_limit=time_limit, presets="medium_quality")


def _score(predictor, df, target: str, feature_cols: list[str], task: str, metric: str):
    m = METRICS[metric]
    y_true = df[target].to_numpy()
    if task == "classification":
        y_pred = predictor.predict_proba(df[feature_cols])[1].to_numpy()
    else:
        y_pred = predictor.predict(df[feature_cols]).to_numpy()
    return float(m.fn(y_true, y_pred)), y_true, y_pred


def run_iteration(dev_df, target: str, feature_cols: list[str], task: str, metric: str,
                  strategy: str = "random", group_key=None, time_col=None,
                  seed: int = 0, held_frac: float = 0.2, time_limit: int = 30,
                  model_dir: str | None = None) -> dict:
    outer_train, outer_val = split(dev_df, strategy=strategy, seed=seed,
                                   held_frac=held_frac, group_key=group_key, time_col=time_col)
    predictor = _fit_predictor(outer_train[feature_cols + [target]], target, task, model_dir, time_limit)
    train_score, _, _ = _score(predictor, outer_train, target, feature_cols, task, metric)
    val_score, val_y_true, val_y_pred = _score(predictor, outer_val, target, feature_cols, task, metric)
    noise_floor = bootstrap_sigma(val_y_true, val_y_pred, metric, seed=seed)
    return {"train_score": train_score, "dev_score": val_score, "noise_floor": noise_floor}


def ceiling_baseline(dev_df, target: str, feature_cols: list[str], task: str, metric: str,
                     human_estimate: float | None = None, seed: int = 0,
                     time_limit: int = 30, model_dir: str | None = None) -> dict:
    # The "proxy" path fits and scores on the SAME full dev_df -- an in-sample
    # training score, not an honest out-of-sample estimate like run_iteration's
    # dev_score. It's optimism-prone by construction; diagnose() treats it as
    # an upper bound, so leaning optimistic is intentional, but don't read it
    # as a real achievable score the way you would run_iteration's dev_score.
    if human_estimate is not None:
        return {"score": float(human_estimate), "source": "human"}
    predictor = _fit_predictor(dev_df[feature_cols + [target]], target, task, model_dir, time_limit)
    score, _, _ = _score(predictor, dev_df, target, feature_cols, task, metric)
    return {"score": score, "source": "proxy"}
