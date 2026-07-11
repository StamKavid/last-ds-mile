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
