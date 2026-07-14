from sealed_bet.auto import ladder_accept


def test_ladder_accept_true_when_improvement_clears_noise_floor_greater_is_better():
    assert ladder_accept(new_score=0.80, best_score=0.76, noise_floor=0.02, greater_is_better=True) is True


def test_ladder_accept_false_when_improvement_within_noise_floor_greater_is_better():
    assert ladder_accept(new_score=0.77, best_score=0.76, noise_floor=0.02, greater_is_better=True) is False


def test_ladder_accept_true_when_improvement_clears_noise_floor_lower_is_better():
    # rmse: lower is better, so an IMPROVEMENT is new_score < best_score
    assert ladder_accept(new_score=0.15, best_score=0.19, noise_floor=0.01, greater_is_better=False) is True


def test_ladder_accept_false_when_regression_metric_gets_worse():
    assert ladder_accept(new_score=0.20, best_score=0.19, noise_floor=0.01, greater_is_better=False) is False


def test_ladder_accept_false_exactly_at_the_boundary():
    # exactly equal to the noise floor is NOT an improvement (strict >), same
    # convention as metrics.py's lift() ship gate (lift > 2.0, not >=).
    # 0.75/0.5/0.25 are exact powers of two, so the subtraction lands exactly
    # on the boundary in IEEE-754 double precision (unlike 0.78 - 0.76).
    assert ladder_accept(new_score=0.75, best_score=0.5, noise_floor=0.25, greater_is_better=True) is False


from sealed_bet.auto import diagnose


def test_diagnose_high_variance_when_train_beats_val_beyond_noise_floor():
    # train 0.91, val 0.72 -- train clearly beats val, well past the noise floor
    result = diagnose(train_score=0.91, val_score=0.72, noise_floor=0.02,
                      ceiling_score=0.95, greater_is_better=True)
    assert result["regime"] == "high_variance"
    assert result["gap"] > 0.02


def test_diagnose_high_bias_when_gap_small_but_val_far_from_ceiling():
    # train 0.77, val 0.76 -- small gap (0.01, within the 0.02 noise floor),
    # but val is far below the ceiling of 0.95 -- still room to improve, not overfitting
    result = diagnose(train_score=0.77, val_score=0.76, noise_floor=0.02,
                      ceiling_score=0.95, greater_is_better=True)
    assert result["regime"] == "high_bias"


def test_diagnose_neither_when_gap_small_and_val_near_ceiling():
    # train 0.94, val 0.93 -- small gap AND val is nearly at the ceiling of 0.95
    result = diagnose(train_score=0.94, val_score=0.93, noise_floor=0.02,
                      ceiling_score=0.95, greater_is_better=True)
    assert result["regime"] == "neither"


def test_diagnose_regimes_for_lower_is_better_metric():
    # rmse: lower is better. train 0.08, val 0.19 -- train "beats" val (lower
    # rmse), well past the noise floor -- high variance
    result = diagnose(train_score=0.08, val_score=0.19, noise_floor=0.01,
                      ceiling_score=0.05, greater_is_better=False)
    assert result["regime"] == "high_variance"

    # train 0.17, val 0.18 -- small gap, but val (0.18) is still far above
    # (worse than) the ceiling of 0.05 -- high bias
    result = diagnose(train_score=0.17, val_score=0.18, noise_floor=0.01,
                      ceiling_score=0.05, greater_is_better=False)
    assert result["regime"] == "high_bias"
