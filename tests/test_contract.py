from sealed_bet.contract import Contract


def _c():
    return Contract(
        target="y", task="classification", metric="roc_auc",
        split={"strategy": "random", "group_key": None, "time_col": None},
        baseline_score=0.5, held_frac=0.2, seed=0, data_hash="abc",
        input_mode="full", created_at="2026-07-10T00:00:00Z",
    )


def test_roundtrip(tmp_path):
    p = tmp_path / "contract.json"
    _c().save(p)
    loaded = Contract.load(p)
    assert loaded.metric == "roc_auc"
    assert loaded.baseline_score == 0.5
    assert loaded.split["strategy"] == "random"


def test_rejects_unknown_metric():
    import pytest
    with pytest.raises(ValueError):
        Contract(
            target="y", task="classification", metric="not_a_metric",
            split={"strategy": "random", "group_key": None, "time_col": None},
            baseline_score=0.5, held_frac=0.2, seed=0, data_hash="abc",
            input_mode="full", created_at="2026-07-10T00:00:00Z",
        ).validate()


def test_rejects_unknown_task():
    import pytest
    c = _c()
    c.task = "clustering"
    with pytest.raises(ValueError, match="task"):
        c.validate()


def test_rejects_non_finite_baseline_score():
    import math
    import pytest
    c = _c()
    c.baseline_score = float("nan")
    with pytest.raises(ValueError, match="baseline_score"):
        c.validate()
    c.baseline_score = math.inf
    with pytest.raises(ValueError, match="baseline_score"):
        c.validate()


def test_rejects_out_of_range_held_frac():
    import pytest
    c = _c()
    c.held_frac = 1.5
    with pytest.raises(ValueError, match="held_frac"):
        c.validate()
    c.held_frac = 0.0
    with pytest.raises(ValueError, match="held_frac"):
        c.validate()


def test_rejects_negative_seed():
    import pytest
    c = _c()
    c.seed = -1
    with pytest.raises(ValueError, match="seed"):
        c.validate()


def test_save_validates_before_writing(tmp_path):
    import pytest
    c = _c()
    c.baseline_score = float("nan")
    with pytest.raises(ValueError):
        c.save(tmp_path / "contract.json")
    assert not (tmp_path / "contract.json").exists()


def test_roundtrip_accepts_str_path(tmp_path):
    p = str(tmp_path / "contract.json")
    _c().save(p)
    loaded = Contract.load(p)
    assert loaded.metric == "roc_auc"
