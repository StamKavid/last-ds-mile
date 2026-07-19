"""Run the credit-card-fraud benchmark under BOTH split strategies and compare.

The point of running two seals rather than one:

`validation-strategy` and `lessons/the-leaderboard-that-lied.md` both say a
time-ordered dataset must be split on time. `BENCHMARKS.md`, separately, queued
this dataset specifically to validate `auto_stratify_col` on a 0.17%-positive
target, which implies a random split. Those two pull in opposite directions, so
this runs both against the same data, the same heuristic baseline, and the same
model budget, and reports the gap.

If the random-split score comes in materially higher, that gap is this project's
own thesis measured on real data: the-leaderboard-that-lied, in numbers, caught
by its own tooling. If it doesn't, that is worth knowing too and gets reported
either way.

Usage:
    uv run python benchmarks/credit-card-fraud/run_benchmark.py --time-limit 300
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))

# `benchmarks/credit-card-fraud` has hyphens, so it is not an importable
# package name; baseline.py sits next to this script and Python puts a script's
# own directory on sys.path, so a flat import is the working form here.
from baseline import anomaly_distance

from sealed_bet.auto import refit_winner
from sealed_bet.score import open_seal
from sealed_bet.seal import seal

DATA = HERE / "creditcard.csv"
TARGET = "Class"
METRIC = "auprc"  # the dataset authors' own recommendation under 0.172% positives

# Community-informed estimate of what an honest, non-leaky model tops out at on
# this dataset's AUPRC. Human-provided on purpose, same convention as the other
# two benchmarks: passing it skips seal()'s AutoGluon proxy-ceiling fit, which
# on 284k rows would cost more than it tells us.
CEILING = 0.85

VARIANTS = {
    "time": dict(strategy="time", time_col="Time"),
    "random": dict(strategy="random", time_col=None),
}


def run_variant(name: str, cfg: dict, time_limit: int) -> dict:
    out = HERE / "last-ds-mile-run" / name
    if out.exists():
        shutil.rmtree(out)  # a seal is one-shot; re-running means starting clean
    out.mkdir(parents=True)
    ledger = out / "LEDGER.md"

    print(f"\n{'=' * 70}\n[{name}] sealing (strategy={cfg['strategy']})\n{'=' * 70}")
    contract = seal(
        str(DATA), target=TARGET, task="classification", metric=METRIC,
        out_dir=str(out), strategy=cfg["strategy"], time_col=cfg["time_col"],
        held_frac=0.2, seed=0, ledger_path=str(ledger),
        ceiling_estimate=CEILING, baseline_fn=anomaly_distance,
        # `Time` is seconds since the first transaction in this particular CSV.
        # It is the key the time split is built from, but it has no meaning at
        # decision time in production -- a deployed scorer never knows how long
        # ago this file started. Excluded from BOTH variants so the only thing
        # differing between them is the split itself.
        exclude_from_features=["Time"],
    )
    print(f"[{name}] baseline={contract.baseline_score:.4f} ({contract.baseline_kind})")

    dev = pd.read_csv(out / "dev.csv")
    held = pd.read_csv(out / "held" / "features.csv")
    feature_cols = [c for c in dev.columns if c != TARGET]

    print(f"[{name}] fitting on dev ({len(dev):,} rows, {int(dev[TARGET].sum())} positives)...")
    predictor = refit_winner(
        dev, TARGET, feature_cols, "classification",
        seed=contract.seed, time_limit=time_limit,
        model_dir=str(out / "auto" / "refit"),
    )
    held_pred = predictor.predict_proba(held[feature_cols], as_multiclass=False).to_numpy()

    # Two columns, row_id echoed from the seal -- predictions are joined on
    # identity, not row position.
    ids = pd.read_csv(out / "held" / "row_ids.csv")["row_id"]
    preds_path = out / "preds.csv"
    pd.DataFrame({"row_id": ids, "pred": held_pred}).to_csv(preds_path, index=False)

    print(f"[{name}] opening the seal (once)...")
    result = open_seal(str(preds_path), str(out), str(ledger))
    result["baseline_kind"] = contract.baseline_kind
    result["held_positives"] = int(pd.read_csv(out / "held" / "_sealed_target.csv")[TARGET].sum())
    result["held_rows"] = len(held)
    result["dev_positives"] = int(dev[TARGET].sum())
    result["dev_rows"] = len(dev)
    print(f"[{name}] {json.dumps(result, indent=2, default=float)}")
    return result


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--time-limit", type=int, default=300, help="AutoGluon seconds per fit")
    ap.add_argument("--variant", choices=[*VARIANTS, "both"], default="both")
    a = ap.parse_args()

    names = list(VARIANTS) if a.variant == "both" else [a.variant]
    results = {n: run_variant(n, VARIANTS[n], a.time_limit) for n in names}

    (HERE / "last-ds-mile-run" / "comparison.json").write_text(
        json.dumps(results, indent=2, default=float), encoding="utf-8"
    )

    print(f"\n{'=' * 70}\nCOMPARISON\n{'=' * 70}")
    hdr = f"{'variant':8} {'sealed':>8} {'baseline':>9} {'sigma':>8} {'lift':>8} {'held+':>6}"
    print(hdr)
    for n, r in results.items():
        print(f"{n:8} {r['sealed_score']:8.4f} {r['baseline']:9.4f} "
              f"{r['sigma']:8.4f} {r['lift']:8.2f} {r['held_positives']:6d}")
    if len(results) == 2:
        gap = results["random"]["sealed_score"] - results["time"]["sealed_score"]
        print(f"\nrandom - time = {gap:+.4f} AUPRC")
        print("A materially positive gap means the random split flattered the model by")
        print("letting it see future transactions -- the-leaderboard-that-lied, measured.")


if __name__ == "__main__":
    main()
