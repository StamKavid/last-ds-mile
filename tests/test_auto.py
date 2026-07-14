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
