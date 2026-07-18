import numpy as np
import pandas as pd
import pytest

from sealed_bet.score import open_seal, reveal
from sealed_bet.seal import seal


def _seal_a_problem(tmp_path):
    df = pd.DataFrame({"x": range(200), "y": [i % 2 for i in range(200)]})
    data = tmp_path / "data.csv"
    df.to_csv(data, index=False)
    out = tmp_path / ".last-ds-mile"
    seal(str(data), "y", "classification", "roc_auc", str(out),
         strategy="random", seed=0, ledger_path=str(tmp_path / "LEDGER.md"),
         ceiling_estimate=0.9)
    return out


def test_open_once_then_refuses_second_open(tmp_path):
    out = _seal_a_problem(tmp_path)
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    pd.DataFrame({"pred": np.full(n, 0.5)}).to_csv(preds, index=False)

    result = open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))
    assert set(["sealed_score", "baseline", "sigma", "lift", "shipped"]).issubset(result)

    with pytest.raises(RuntimeError, match="already opened"):
        open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))


def test_open_seal_writes_a_revealed_csv_for_post_hoc_analysis(tmp_path):
    # /ds-evaluate and /ds-explain's own SKILL.md instruct producing a slice
    # table and feature importance "on the held set" -- this is the sanctioned
    # path for that now that the bet is settled, instead of no path at all.
    out = _seal_a_problem(tmp_path)
    held = pd.read_csv(out / "held" / "features.csv")
    n = len(held)
    preds = tmp_path / "preds.csv"
    model_preds = (held["x"].to_numpy() % 2).astype(float)  # this dataset's y IS x % 2
    pd.DataFrame({"pred": model_preds}).to_csv(preds, index=False)

    open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))

    revealed_path = out / "held" / "revealed.csv"
    assert revealed_path.exists()
    revealed = pd.read_csv(revealed_path)
    assert list(revealed.columns) == ["y", "pred"]
    assert len(revealed) == n
    assert np.array_equal(revealed["pred"].to_numpy(), model_preds)
    # row order matches held/features.csv, so it can be joined with it directly
    assert np.array_equal(revealed["y"].to_numpy(), model_preds)  # y IS x % 2 here


def test_revealed_csv_is_not_blocked_by_the_seal_guard(tmp_path):
    import json
    import subprocess
    import sys as _sys
    from pathlib import Path

    out = _seal_a_problem(tmp_path)
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    pd.DataFrame({"pred": np.full(n, 0.5)}).to_csv(preds, index=False)
    open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))

    hook = Path(__file__).resolve().parents[1] / "hooks" / "seal_guard.py"
    payload = json.dumps({"tool_name": "Read",
                          "tool_input": {"file_path": str(out / "held" / "revealed.csv")}})
    proc = subprocess.run([_sys.executable, str(hook)], input=payload,
                         capture_output=True, text=True)
    assert '"deny"' not in proc.stdout


def test_reveal_refuses_before_the_seal_is_opened(tmp_path):
    out = _seal_a_problem(tmp_path)
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    pd.DataFrame({"pred": np.full(n, 0.5)}).to_csv(preds, index=False)
    with pytest.raises(RuntimeError, match="refuses to run before"):
        reveal(str(out), str(preds))


def test_reveal_can_backfill_an_already_opened_seal(tmp_path):
    # The exact situation this was built for: a seal opened before reveal()
    # existed. reveal() must still work standalone once is_opened is True.
    out = _seal_a_problem(tmp_path)
    held = pd.read_csv(out / "held" / "features.csv")
    preds = tmp_path / "preds.csv"
    model_preds = (held["x"].to_numpy() % 2).astype(float)
    pd.DataFrame({"pred": model_preds}).to_csv(preds, index=False)
    open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))

    (out / "held" / "revealed.csv").unlink()  # simulate a pre-reveal() historical seal
    revealed_path = reveal(str(out), str(preds))
    assert revealed_path == out / "held" / "revealed.csv"
    assert revealed_path.exists()


def test_constant_pred_does_not_ship(tmp_path):
    out = _seal_a_problem(tmp_path)
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    pd.DataFrame({"pred": np.full(n, 0.5)}).to_csv(preds, index=False)
    result = open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))
    assert result["shipped"] is False  # no lift over a constant baseline


def test_open_seal_raises_a_clear_error_when_baseline_preds_missing(tmp_path):
    # Simulates a seal written before the paired-baseline fix: contract.json
    # and _sealed_target.csv exist but _sealed_baseline_preds.csv doesn't.
    # This must fail loudly, not silently fall back to a meaningless sigma --
    # the same "explain, don't guess" pattern Contract.load already uses for
    # a pre-Phase-C contract.json.
    out = _seal_a_problem(tmp_path)
    (out / "held" / "_sealed_baseline_preds.csv").unlink()
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    pd.DataFrame({"pred": np.full(n, 0.5)}).to_csv(preds, index=False)
    with pytest.raises(FileNotFoundError, match="_sealed_baseline_preds"):
        open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))


def test_open_seal_against_a_heuristic_baseline_uses_paired_sigma(tmp_path):
    # A model that's only marginally better than a strong heuristic baseline
    # should ship with a modest, not astronomical, lift -- proving the paired
    # sigma (and a real baseline_fn) actually constrains the verdict, instead
    # of every non-broken model scoring 20-30 sigma against a constant 0.5.
    df = pd.DataFrame({"x": range(300), "y": [i % 2 for i in range(300)]})
    data = tmp_path / "data.csv"
    df.to_csv(data, index=False)
    out = tmp_path / ".last-ds-mile"

    def heuristic(dev_df, held_features_df):
        return (held_features_df["x"].to_numpy() % 2).astype(float)  # this dataset's y IS x % 2

    contract = seal(str(data), "y", "classification", "roc_auc", str(out),
                    strategy="random", seed=0, ledger_path=str(tmp_path / "LEDGER.md"),
                    ceiling_estimate=0.99, baseline_fn=heuristic)
    assert contract.baseline_score > 0.9  # the heuristic already nails this dataset

    held = pd.read_csv(out / "held" / "features.csv")
    # a model barely better than the heuristic on a couple of rows
    model_preds = (held["x"].to_numpy() % 2).astype(float)
    model_preds[:2] = 1.0 - model_preds[:2]
    preds_path = tmp_path / "preds.csv"
    pd.DataFrame({"pred": model_preds}).to_csv(preds_path, index=False)

    result = open_seal(str(preds_path), str(out), str(tmp_path / "LEDGER.md"))
    assert result["lift"] < 20.0  # nowhere near the old constant-baseline-style blowout
