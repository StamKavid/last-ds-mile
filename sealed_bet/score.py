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


def _read_predictions(preds_path: str, out_dir: str, n_expected: int,
                      unsafe_positional_join: bool = False) -> np.ndarray:
    """Read preds.csv and return predictions in held-set order.

    The bug this exists to close: predictions used to be joined to sealed
    labels purely by ROW POSITION (`pd.read_csv(preds).iloc[:, 0]`). Row count
    was checked, order never was. Any pipeline that sorted, grouped, reindexed,
    or shuffled before writing preds.csv would score against the wrong labels
    silently -- no error, just a confidently wrong verdict with no way to
    detect it after the fact. For a tool whose entire purpose is refusing to
    trust an unearned number, that was the worst available failure mode.

    Seals written by current code ship `held/row_ids.csv`. When it is present,
    preds.csv MUST carry a `row_id` column echoing those ids; predictions are
    then reindexed into held order and any mismatch raises. Seals predating
    that file fall back to the positional read, since there is nothing better
    available for them.
    """
    preds_df = pd.read_csv(preds_path)
    row_ids_path = Path(out_dir) / "held" / "row_ids.csv"

    if unsafe_positional_join or not row_ids_path.exists():
        if len(preds_df) != n_expected:
            raise ValueError(f"preds ({len(preds_df)}) != sealed rows ({n_expected})")
        return preds_df.iloc[:, 0].to_numpy()

    expected = pd.read_csv(row_ids_path)["row_id"].to_numpy()

    if "row_id" not in preds_df.columns:
        raise ValueError(
            f"{preds_path} has no 'row_id' column. This seal records row identity "
            f"in {row_ids_path}, and predictions are joined on it so that a "
            f"reordered prediction file cannot be scored against the wrong labels. "
            f"Write preds.csv as two columns, row_id and pred:\n"
            f"    ids = pd.read_csv('{row_ids_path.as_posix()}')['row_id']\n"
            f"    pd.DataFrame({{'row_id': ids, 'pred': preds}}).to_csv(preds_path, index=False)\n"
            f"If you are certain your predictions are in the exact row order of "
            f"held/features.csv, --unsafe-positional-join restores the old behavior."
        )

    pred_cols = [c for c in preds_df.columns if c != "row_id"]
    if len(pred_cols) != 1:
        raise ValueError(
            f"{preds_path} must have exactly one prediction column alongside "
            f"'row_id', found {pred_cols}"
        )

    if preds_df["row_id"].duplicated().any():
        dupes = preds_df.loc[preds_df["row_id"].duplicated(), "row_id"].unique()
        raise ValueError(
            f"{preds_path} has duplicate row_id values (e.g. {list(dupes[:5])}) — "
            f"each held row must have exactly one prediction"
        )

    got = set(preds_df["row_id"].to_numpy().tolist())
    want = set(expected.tolist())
    if got != want:
        missing, extra = sorted(want - got), sorted(got - want)
        raise ValueError(
            f"{preds_path}'s row_ids do not match the sealed held set: "
            f"{len(missing)} missing (e.g. {missing[:5]}), "
            f"{len(extra)} unexpected (e.g. {extra[:5]}). Predictions must cover "
            f"every held row exactly once."
        )

    # Reindex into held order. Order in preds.csv itself is now irrelevant --
    # which is the entire point.
    return preds_df.set_index("row_id").loc[expected, pred_cols[0]].to_numpy()


def score_dev(y_true, y_pred, metric_name: str, ledger_path=None, note: str = "") -> float:
    m = METRICS[metric_name]
    score = float(m.fn(np.asarray(y_true), np.asarray(y_pred)))
    if ledger_path:
        append_experiment(ledger_path, note or "experiment", score)
    return score


def reveal(out_dir: str, preds_path: str, unsafe_positional_join: bool = False) -> Path:
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
    preds = _read_predictions(preds_path, out_dir, len(y_true), unsafe_positional_join)
    revealed_path = Path(out_dir) / "held" / "revealed.csv"
    pd.DataFrame({contract.target: y_true, "pred": preds}).to_csv(revealed_path, index=False)
    return revealed_path


def open_seal(preds_path: str, out_dir: str, ledger_path: str,
              unsafe_positional_join: bool = False) -> dict:
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
    # The baseline predictions are written by seal() in held order and never
    # leave this package, so they need no identity check -- unlike preds.csv,
    # which round-trips through the user's own pipeline.
    y_base = pd.read_csv(baseline_path).iloc[:, 0].to_numpy()
    preds = _read_predictions(preds_path, out_dir, len(y_true), unsafe_positional_join)

    sealed = float(m.fn(y_true, preds))
    sigma = paired_bootstrap_sigma(y_true, preds, y_base, contract.metric, seed=contract.seed)
    lift_val = lift(sealed, contract.baseline_score, sigma, m.greater_is_better)
    shipped = lift_val > SHIP_THRESHOLD

    mark_opened(out_dir)
    append_verdict(ledger_path, sealed, contract.baseline_score, sigma, lift_val, shipped)
    reveal(out_dir, preds_path, unsafe_positional_join)
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
    ap.add_argument(
        "--preds", required=True,
        help="CSV of predictions on held/features.csv. Two columns: row_id "
             "(echoed from held/row_ids.csv) and the prediction.",
    )
    ap.add_argument("--out", default=".last-ds-mile")
    ap.add_argument("--ledger", default="LEDGER.md")
    ap.add_argument(
        "--unsafe-positional-join", action="store_true",
        help="Join predictions to sealed labels by row POSITION instead of "
             "row_id. Only for seals written before row_ids.csv existed, or "
             "when you are certain preds.csv is in exact held-set order. A "
             "reordered file scores against the wrong labels silently.",
    )
    a = ap.parse_args()
    r = open_seal(a.preds, a.out, a.ledger, a.unsafe_positional_join)
    verdict = "SHIP" if r["shipped"] else "DO NOT SHIP"
    print(f"lift={r['lift']:.2f}σ  sealed={r['sealed_score']:.4f}  "
          f"baseline={r['baseline']:.4f}  → {verdict}")


if __name__ == "__main__":
    main()
