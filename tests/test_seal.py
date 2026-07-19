import numpy as np
import pandas as pd
import pytest
from helpers import requires_autogluon

from sealed_bet.seal import seal


def _write_csv(tmp_path):
    df = pd.DataFrame({"x": range(100), "y": [i % 2 for i in range(100)]})
    p = tmp_path / "data.csv"
    df.to_csv(p, index=False)
    return p


def test_seal_creates_artifacts_and_hides_labels(tmp_path):
    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    seal(str(data), target="y", task="classification", metric="roc_auc",
         out_dir=str(out), strategy="random", seed=0,
         ledger_path=str(tmp_path / "LEDGER.md"), ceiling_estimate=0.9)

    assert (out / "contract.json").exists()
    assert (out / "dev.csv").exists()
    assert (out / "held" / "features.csv").exists()
    assert (out / "held" / "_sealed_target.csv").exists()
    # the readable held features must NOT contain the target column
    feats = pd.read_csv(out / "held" / "features.csv")
    assert "y" not in feats.columns
    # ledger header written
    assert "Contract" in (tmp_path / "LEDGER.md").read_text(encoding="utf-8")


def test_reseal_after_open_does_not_destroy_prior_holdout(tmp_path):
    import pytest

    from sealed_bet.state import mark_opened

    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    seal(str(data), target="y", task="classification", metric="roc_auc",
         out_dir=str(out), strategy="random", seed=0, ledger_path=str(led), ceiling_estimate=0.9)

    original_target_bytes = (out / "held" / "_sealed_target.csv").read_bytes()
    original_contract_bytes = (out / "contract.json").read_bytes()
    mark_opened(out)

    with pytest.raises(RuntimeError, match="already opened"):
        seal(str(data), target="y", task="classification", metric="roc_auc",
             out_dir=str(out), strategy="random", seed=1, ledger_path=str(led), ceiling_estimate=0.9)

    # the ORIGINAL sealed holdout must be completely untouched by the refused re-seal
    assert (out / "held" / "_sealed_target.csv").read_bytes() == original_target_bytes
    assert (out / "contract.json").read_bytes() == original_contract_bytes


def test_seal_records_a_probe_verdict_in_the_ledger(tmp_path):
    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    seal(str(data), target="y", task="classification", metric="roc_auc",
         out_dir=str(out), strategy="random", seed=0, ledger_path=str(led), ceiling_estimate=0.9)
    text = led.read_text(encoding="utf-8")
    assert "train-vs-held AUC" in text
    assert "probe skipped" not in text.lower()


def test_seal_survives_a_probe_failure(tmp_path, monkeypatch):
    import sealed_bet.seal as seal_module

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated probe failure")

    monkeypatch.setattr(seal_module, "split_adversary", _boom)

    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    # seal() must still succeed and write its core artifacts even if the probe blows up
    contract = seal(str(data), target="y", task="classification", metric="roc_auc",
                    out_dir=str(out), strategy="random", seed=0, ledger_path=str(led), ceiling_estimate=0.9)
    assert (out / "contract.json").exists()
    assert contract.metric == "roc_auc"
    text = led.read_text(encoding="utf-8")
    assert "probe skipped" in text.lower()


def test_seal_records_budget_and_ceiling_with_human_estimate(tmp_path):
    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    contract = seal(str(data), target="y", task="classification", metric="roc_auc",
                    out_dir=str(out), strategy="random", seed=0, ledger_path=str(led),
                    budget=10, ceiling_estimate=0.95)
    assert contract.budget == 10
    assert contract.ceiling_score == 0.95
    assert contract.ceiling_source == "human"
    text = led.read_text(encoding="utf-8")
    assert "ceiling_score" in text


@requires_autogluon
def test_seal_computes_ceiling_proxy_when_no_estimate_given(tmp_path):
    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    contract = seal(str(data), target="y", task="classification", metric="roc_auc",
                    out_dir=str(out), strategy="random", seed=0, ledger_path=str(led),
                    ceiling_estimate=None)
    assert contract.ceiling_source == "proxy"
    assert 0.0 <= contract.ceiling_score <= 1.0
    assert contract.budget == 15  # default


def test_seal_defaults_budget_to_15_when_not_specified(tmp_path):
    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    contract = seal(str(data), target="y", task="classification", metric="roc_auc",
                    out_dir=str(out), strategy="random", seed=0, ledger_path=str(led),
                    ceiling_estimate=0.9)
    assert contract.budget == 15


def test_seal_writes_a_sealed_baseline_predictions_file(tmp_path):
    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    seal(str(data), target="y", task="classification", metric="roc_auc",
         out_dir=str(out), strategy="random", seed=0,
         ledger_path=str(tmp_path / "LEDGER.md"), ceiling_estimate=0.9)
    preds_path = out / "held" / "_sealed_baseline_preds.csv"
    assert preds_path.exists()
    preds = pd.read_csv(preds_path)
    held = pd.read_csv(out / "held" / "features.csv")
    assert len(preds) == len(held)  # one baseline prediction per held row


def test_seal_default_baseline_is_constant_kind(tmp_path):
    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    contract = seal(str(data), target="y", task="classification", metric="roc_auc",
                    out_dir=str(out), strategy="random", seed=0,
                    ledger_path=str(tmp_path / "LEDGER.md"), ceiling_estimate=0.9)
    assert contract.baseline_kind == "constant"
    assert contract.baseline_score == pytest.approx(0.5)  # constant probability -> 0.5 AUC


def test_seal_accepts_a_heuristic_baseline_fn(tmp_path):
    # A real non-ML rival, not a constant -- the actual bar /ds-baseline
    # names in prose ("target every month-to-month customer",
    # "$/sqft by neighborhood") but never previously got to score against.
    def heuristic(dev_df, held_features_df):
        return (held_features_df["x"].to_numpy() % 2).astype(float)  # this dataset's y IS x % 2

    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    contract = seal(str(data), target="y", task="classification", metric="roc_auc",
                    out_dir=str(out), strategy="random", seed=0,
                    ledger_path=str(tmp_path / "LEDGER.md"), ceiling_estimate=0.9,
                    baseline_fn=heuristic)
    assert contract.baseline_kind == "heuristic"
    # this dataset's y is literally x % 2, so the heuristic should score near-perfectly
    assert contract.baseline_score > 0.9


def test_seal_rejects_a_baseline_fn_with_wrong_length(tmp_path):
    def bad_heuristic(dev_df, held_features_df):
        return [0.5] * (len(held_features_df) - 1)

    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    with pytest.raises(ValueError, match="held rows"):
        seal(str(data), target="y", task="classification", metric="roc_auc",
             out_dir=str(out), strategy="random", seed=0,
             ledger_path=str(tmp_path / "LEDGER.md"), ceiling_estimate=0.9,
             baseline_fn=bad_heuristic)


def test_seal_records_a_leakage_probe_verdict_in_the_ledger(tmp_path):
    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    seal(str(data), target="y", task="classification", metric="roc_auc",
         out_dir=str(out), strategy="random", seed=0, ledger_path=str(led), ceiling_estimate=0.9)
    text = led.read_text(encoding="utf-8")
    assert "leakage-adversary" in text


def test_seal_leakage_probe_survives_categorical_and_missing_data(tmp_path):
    # The regression case: both probes used to crash on the first string
    # column or NaN, which is every realistic dataset. Confirm seal() gets
    # a real verdict (not a "probe skipped" fallback) end to end.
    n = 150
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "num": rng.normal(size=n),
        "num_with_gaps": np.where(rng.random(n) < 0.1, np.nan, rng.normal(size=n)),
        "cat": rng.choice(["A", "B", "C"], size=n),
        "y": rng.integers(0, 2, size=n),
    })
    data = tmp_path / "mixed.csv"
    df.to_csv(data, index=False)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    seal(str(data), target="y", task="classification", metric="roc_auc",
         out_dir=str(out), strategy="random", seed=0, ledger_path=str(led), ceiling_estimate=0.9)
    text = led.read_text(encoding="utf-8")
    assert "probe skipped" not in text.lower()
    assert "leakage-adversary" in text
    assert "train-vs-held AUC" in text


def test_seal_skips_split_adversary_for_time_strategy(tmp_path):
    # A time split's dev/held ARE supposed to be distinguishable (held is
    # always later) -- running split_adversary there would reliably produce a
    # false-positive "SUSPECT" verdict, so seal() must skip it outright rather
    # than log a misleading number.
    # y is independent noise, not a function of t/x -- keeps the (unrelated)
    # leakage-adversary probe CLEAR so this test isolates the split-adversary
    # skip behavior instead of entangling it with a real, correct leakage flag.
    n = 100
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "t": range(n), "x": range(n), "y": rng.normal(size=n),
    })
    data = tmp_path / "data.csv"
    df.to_csv(data, index=False)
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    seal(str(data), target="y", task="regression", metric="rmse",
         out_dir=str(out), strategy="time", time_col="t", seed=0,
         ledger_path=str(led), ceiling_estimate=1.0)
    text = led.read_text(encoding="utf-8")
    split_adversary_section = text.split("## Probe (split-adversary")[1]
    assert "N/A" in split_adversary_section
    assert "train-vs-held AUC" not in split_adversary_section  # never run
    assert "SUSPECT" not in split_adversary_section


def test_seal_runs_split_adversary_normally_for_random_strategy(tmp_path):
    out = tmp_path / ".last-ds-mile"
    led = tmp_path / "LEDGER.md"
    data = _write_csv(tmp_path)
    seal(str(data), target="y", task="classification", metric="roc_auc",
         out_dir=str(out), strategy="random", seed=0, ledger_path=str(led), ceiling_estimate=0.9)
    text = led.read_text(encoding="utf-8")
    assert "train-vs-held AUC" in text
    assert "N/A" not in text


def test_seal_excludes_columns_from_features_but_keeps_them_out_of_the_frames(tmp_path):
    n = 100
    df = pd.DataFrame({
        "t": range(n), "x": range(n), "y": [float(i) for i in range(n)],
    })
    data = tmp_path / "data.csv"
    df.to_csv(data, index=False)
    out = tmp_path / ".last-ds-mile"
    contract = seal(str(data), target="y", task="regression", metric="rmse",
                    out_dir=str(out), strategy="time", time_col="t", seed=0,
                    ledger_path=str(tmp_path / "LEDGER.md"), ceiling_estimate=1.0,
                    exclude_from_features=["t"])
    assert contract.excluded_features == ["t"]
    dev = pd.read_csv(out / "dev.csv")
    held = pd.read_csv(out / "held" / "features.csv")
    assert "t" not in dev.columns
    assert "t" not in held.columns
    assert "x" in dev.columns and "x" in held.columns  # only the excluded column is gone


def test_seal_default_has_no_excluded_features(tmp_path):
    data = _write_csv(tmp_path)
    out = tmp_path / ".last-ds-mile"
    contract = seal(str(data), target="y", task="classification", metric="roc_auc",
                    out_dir=str(out), strategy="random", seed=0,
                    ledger_path=str(tmp_path / "LEDGER.md"), ceiling_estimate=0.9)
    assert contract.excluded_features == []
