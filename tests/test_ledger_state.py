from sealed_bet.state import init_state, is_opened, mark_opened
from sealed_bet.ledger import write_header, append_experiment, append_verdict, append_probe
from sealed_bet.contract import Contract


def _c():
    return Contract("y", "classification", "roc_auc",
                    {"strategy": "random", "group_key": None, "time_col": None},
                    0.5, 0.2, 0, "abc", "full", "2026-07-10T00:00:00Z")


def test_open_once_flag(tmp_path):
    init_state(tmp_path)
    assert is_opened(tmp_path) is False
    mark_opened(tmp_path)
    assert is_opened(tmp_path) is True


def test_ledger_records_header_experiments_verdict(tmp_path):
    led = tmp_path / "LEDGER.md"
    write_header(led, _c())
    append_experiment(led, "logreg on 3 features", dev_score=0.83)
    append_verdict(led, sealed_score=0.50, baseline_score=0.50, sigma=0.05,
                   lift_val=0.0, shipped=False)
    text = led.read_text(encoding="utf-8")
    assert "roc_auc" in text
    assert "logreg on 3 features" in text
    assert "NOT SHIPPED" in text
    assert "lift" in text.lower()


def test_init_state_refuses_to_reset_opened_seal(tmp_path):
    import pytest
    init_state(tmp_path)
    mark_opened(tmp_path)
    with pytest.raises(RuntimeError, match="already opened"):
        init_state(tmp_path)
    # the seal must still read as opened after the refused re-init attempt
    assert is_opened(tmp_path) is True


def test_init_state_allows_reset_before_opening(tmp_path):
    init_state(tmp_path)
    init_state(tmp_path)  # calling twice before opening is fine, not dangerous
    assert is_opened(tmp_path) is False


def test_is_opened_fails_loud_on_corrupted_state(tmp_path):
    import pytest
    (tmp_path / "seal_state.json").write_text("{not valid json", encoding="utf-8")
    with pytest.raises(RuntimeError, match="corrupted"):
        is_opened(tmp_path)


def test_is_opened_fails_loud_on_non_bool_opened_value(tmp_path):
    import pytest
    (tmp_path / "seal_state.json").write_text('{"opened": "false"}', encoding="utf-8")
    with pytest.raises(RuntimeError, match="corrupted"):
        is_opened(tmp_path)


def test_is_opened_fails_loud_on_missing_opened_key(tmp_path):
    import pytest
    (tmp_path / "seal_state.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="corrupted"):
        is_opened(tmp_path)


def test_is_opened_fails_loud_on_non_dict_json(tmp_path):
    import pytest
    for content in ("[1, 2, 3]", "42", '"just a string"', "null", "true"):
        (tmp_path / "seal_state.json").write_text(content, encoding="utf-8")
        with pytest.raises(RuntimeError, match="corrupted"):
            is_opened(tmp_path)


def test_init_state_refuses_when_state_is_corrupted(tmp_path):
    import pytest
    (tmp_path / "seal_state.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="corrupted"):
        init_state(tmp_path)


def test_ledger_records_probe_verdict(tmp_path):
    led = tmp_path / "LEDGER.md"
    write_header(led, _c())
    append_probe(led, auc=0.51, sigma=0.05, lift_val=0.2, certified=True)
    text = led.read_text(encoding="utf-8")
    assert "Probe" in text
    assert "CERTIFIED" in text
