from sealed_bet.state import init_state, is_opened, mark_opened
from sealed_bet.ledger import write_header, append_experiment, append_verdict
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
