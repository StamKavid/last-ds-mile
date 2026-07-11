"""score_dev(): score a dev fold. open_seal(): open the holdout ONCE and judge by lift."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from sealed_bet.contract import Contract
from sealed_bet.ledger import append_experiment, append_verdict
from sealed_bet.metrics import METRICS, bootstrap_sigma, lift
from sealed_bet.state import is_opened, mark_opened

SHIP_THRESHOLD = 2.0


def score_dev(y_true, y_pred, metric_name: str, ledger_path=None, note: str = "") -> float:
    m = METRICS[metric_name]
    score = float(m.fn(np.asarray(y_true), np.asarray(y_pred)))
    if ledger_path:
        append_experiment(ledger_path, note or "experiment", score)
    return score


def open_seal(preds_path: str, out_dir: str, ledger_path: str) -> dict:
    if is_opened(out_dir):
        raise RuntimeError("seal already opened — the bet is settled; re-seal to run again")

    contract = Contract.load(Path(out_dir) / "contract.json")
    m = METRICS[contract.metric]
    y_true = pd.read_csv(Path(out_dir) / "held" / "_sealed_target.csv")[contract.target].to_numpy()
    preds = pd.read_csv(preds_path).iloc[:, 0].to_numpy()
    if len(preds) != len(y_true):
        raise ValueError(f"preds ({len(preds)}) != sealed rows ({len(y_true)})")

    sealed = float(m.fn(y_true, preds))
    sigma = bootstrap_sigma(y_true, preds, contract.metric, seed=contract.seed)
    lift_val = lift(sealed, contract.baseline_score, sigma, m.greater_is_better)
    shipped = lift_val > SHIP_THRESHOLD

    append_verdict(ledger_path, sealed, contract.baseline_score, sigma, lift_val, shipped)
    mark_opened(out_dir)
    return {"sealed_score": sealed, "baseline": contract.baseline_score,
            "sigma": sigma, "lift": lift_val, "shipped": shipped}


def main() -> None:
    ap = argparse.ArgumentParser(prog="sealed_bet.score")
    ap.add_argument("--preds", required=True, help="CSV of predictions on held/features.csv")
    ap.add_argument("--out", default=".last-ds-mile")
    ap.add_argument("--ledger", default="LEDGER.md")
    a = ap.parse_args()
    r = open_seal(a.preds, a.out, a.ledger)
    verdict = "SHIP" if r["shipped"] else "DO NOT SHIP"
    print(f"lift={r['lift']:.2f}σ  sealed={r['sealed_score']:.4f}  "
          f"baseline={r['baseline']:.4f}  → {verdict}")


if __name__ == "__main__":
    main()
