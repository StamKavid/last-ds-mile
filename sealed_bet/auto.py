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
