from sealed_bet.contract import Contract


def _c():
    return Contract(
        target="y", task="classification", metric="roc_auc",
        split={"strategy": "random", "group_key": None, "time_col": None},
        baseline_score=0.5, baseline_kind="constant", held_frac=0.2, seed=0, data_hash="abc",
        input_mode="full", created_at="2026-07-10T00:00:00Z",
        budget=15, ceiling_score=0.5, ceiling_source="proxy",
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
            baseline_score=0.5, baseline_kind="constant", held_frac=0.2, seed=0, data_hash="abc",
            input_mode="full", created_at="2026-07-10T00:00:00Z",
            budget=15, ceiling_score=0.5, ceiling_source="proxy",
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


def test_rejects_unknown_baseline_kind():
    import pytest
    c = _c()
    c.baseline_kind = "vibes"
    with pytest.raises(ValueError, match="baseline_kind"):
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


def test_contract_validates_budget_and_ceiling_fields():
    c = Contract(
        target="y", task="classification", metric="roc_auc",
        split={"strategy": "random", "group_key": None, "time_col": None},
        baseline_score=0.5, baseline_kind="constant", held_frac=0.2, seed=0, data_hash="abc",
        input_mode="full", created_at="2026-07-13T00:00:00Z",
        budget=15, ceiling_score=0.9, ceiling_source="human",
    )
    c.validate()  # must not raise
    assert c.budget == 15
    assert c.ceiling_score == 0.9
    assert c.ceiling_source == "human"


def test_contract_rejects_non_positive_budget():
    import pytest
    c = Contract(
        target="y", task="classification", metric="roc_auc",
        split={"strategy": "random", "group_key": None, "time_col": None},
        baseline_score=0.5, baseline_kind="constant", held_frac=0.2, seed=0, data_hash="abc",
        input_mode="full", created_at="2026-07-13T00:00:00Z",
        budget=0, ceiling_score=0.9, ceiling_source="human",
    )
    with pytest.raises(ValueError, match="budget"):
        c.validate()


def test_contract_rejects_non_finite_ceiling_score():
    import pytest
    c = Contract(
        target="y", task="classification", metric="roc_auc",
        split={"strategy": "random", "group_key": None, "time_col": None},
        baseline_score=0.5, baseline_kind="constant", held_frac=0.2, seed=0, data_hash="abc",
        input_mode="full", created_at="2026-07-13T00:00:00Z",
        budget=15, ceiling_score=float("nan"), ceiling_source="human",
    )
    with pytest.raises(ValueError, match="ceiling_score"):
        c.validate()


def test_contract_rejects_unknown_ceiling_source():
    import pytest
    c = Contract(
        target="y", task="classification", metric="roc_auc",
        split={"strategy": "random", "group_key": None, "time_col": None},
        baseline_score=0.5, baseline_kind="constant", held_frac=0.2, seed=0, data_hash="abc",
        input_mode="full", created_at="2026-07-13T00:00:00Z",
        budget=15, ceiling_score=0.9, ceiling_source="guess",
    )
    with pytest.raises(ValueError, match="ceiling_source"):
        c.validate()


def test_excluded_features_defaults_to_empty_list():
    c = _c()
    assert c.excluded_features == []
    c.validate()  # must not raise


def test_rejects_non_list_excluded_features():
    import pytest
    c = _c()
    c.excluded_features = "t"  # a bare string, not a list -- iterating it would silently
                               # treat each character as a column name
    with pytest.raises(ValueError, match="excluded_features"):
        c.validate()


def test_rejects_target_in_excluded_features():
    import pytest
    c = _c()
    c.excluded_features = [c.target]
    with pytest.raises(ValueError, match="excluded_features"):
        c.validate()


def test_roundtrips_excluded_features(tmp_path):
    c = _c()
    c.excluded_features = ["t", "raw_timestamp"]
    p = tmp_path / "contract.json"
    c.save(p)
    loaded = Contract.load(p)
    assert loaded.excluded_features == ["t", "raw_timestamp"]
