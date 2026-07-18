"""score_dev(): score a dev fold. open_seal(): open the holdout ONCE and judge by lift."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sealed_bet.contract import Contract
from sealed_bet.ledger import append_experiment, append_verdict
from sealed_bet.metrics import METRICS, lift, paired_bootstrap_sigma
from sealed_bet.state import is_opened, mark_opened

SHIP_THRESHOLD = 2.0


def score_dev(y_true, y_pred, metric_name: str, ledger_path=None, note: str = "") -> float:
    m = METRICS[metric_name]
    score = float(m.fn(np.asarray(y_true), np.asarray(y_pred)))
    if ledger_path:
        append_experiment(ledger_path, note or "experiment", score)
    return score


def reveal(out_dir: str, preds_path: str) -> Path:
    """Write held/revealed.csv (the true target + submitted predictions), for
    a seal that is ALREADY opened.

    This exists because /ds-evaluate and /ds-explain's own SKILL.md instruct
    producing a slice table, calibration check, and feature importance "on the
    held set" -- but before this, there was no sanctioned way to get held
    labels at all: open_seal() only ever returned an aggregate
    {sealed_score, baseline, sigma, lift, shipped} dict. Once the seal is
    opened, the one-look guarantee has already been spent -- the ship/no-ship
    verdict is irrevocably logged -- so writing the labels out for legitimate
    post-hoc analysis doesn't re-open any question the guard exists to
    protect. Refusing to run before opening is the one invariant that matters
    here: this must never become a second way to peek.

    held/revealed.csv is NOT under the seal_guard's `_sealed*` naming pattern,
    so it's readable by the ordinary Read tool once written -- deliberately;
    that's the whole point of calling this "revealed" rather than "sealed".
    """
    if not is_opened(out_dir):
        raise RuntimeError(
            "reveal() refuses to run before the seal is opened — call "
            "open_seal() first. Revealing held labels before that would be "
            "exactly the leak this project's guard exists to prevent."
        )
    contract = Contract.load(Path(out_dir) / "contract.json")
    y_true = pd.read_csv(Path(out_dir) / "held" / "_sealed_target.csv")[contract.target].to_numpy()
    preds = pd.read_csv(preds_path).iloc[:, 0].to_numpy()
    if len(preds) != len(y_true):
        raise ValueError(f"preds ({len(preds)}) != sealed rows ({len(y_true)})")
    revealed_path = Path(out_dir) / "held" / "revealed.csv"
    pd.DataFrame({contract.target: y_true, "pred": preds}).to_csv(revealed_path, index=False)
    return revealed_path


def open_seal(preds_path: str, out_dir: str, ledger_path: str) -> dict:
    if is_opened(out_dir):
        raise RuntimeError("seal already opened — the bet is settled; re-seal to run again")

    contract = Contract.load(Path(out_dir) / "contract.json")
    m = METRICS[contract.metric]
    y_true = pd.read_csv(Path(out_dir) / "held" / "_sealed_target.csv")[contract.target].to_numpy()
    baseline_path = Path(out_dir) / "held" / "_sealed_baseline_preds.csv"
    if not baseline_path.exists():
        raise FileNotFoundError(
            f"{baseline_path} is missing — this seal predates the paired-baseline "
            f"fix and can't be opened with a real σ; re-run /ds-seal on this data "
            f"to write it, then rebuild before opening"
        )
    y_base = pd.read_csv(baseline_path).iloc[:, 0].to_numpy()
    preds = pd.read_csv(preds_path).iloc[:, 0].to_numpy()
    if len(preds) != len(y_true):
        raise ValueError(f"preds ({len(preds)}) != sealed rows ({len(y_true)})")

    sealed = float(m.fn(y_true, preds))
    sigma = paired_bootstrap_sigma(y_true, preds, y_base, contract.metric, seed=contract.seed)
    lift_val = lift(sealed, contract.baseline_score, sigma, m.greater_is_better)
    shipped = lift_val > SHIP_THRESHOLD

    mark_opened(out_dir)
    append_verdict(ledger_path, sealed, contract.baseline_score, sigma, lift_val, shipped)
    reveal(out_dir, preds_path)
    return {"sealed_score": sealed, "baseline": contract.baseline_score,
            "sigma": sigma, "lift": lift_val, "shipped": shipped}


def main() -> None:
    # The verdict itself is written to LEDGER.md (UTF-8) before this runs; without
    # this, a Windows console on a non-UTF-8 codepage (cp1252, the default) crashes
    # on the sigma/arrow glyphs below -- discovered when this exact command failed
    # after a real, successful seal-opening on this platform.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
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
