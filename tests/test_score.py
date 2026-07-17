import numpy as np
import pandas as pd
import pytest

from sealed_bet.seal import seal
from sealed_bet.score import open_seal


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


def test_constant_pred_does_not_ship(tmp_path):
    out = _seal_a_problem(tmp_path)
    n = len(pd.read_csv(out / "held" / "features.csv"))
    preds = tmp_path / "preds.csv"
    pd.DataFrame({"pred": np.full(n, 0.5)}).to_csv(preds, index=False)
    result = open_seal(str(preds), str(out), str(tmp_path / "LEDGER.md"))
    assert result["shipped"] is False  # no lift over a constant baseline
