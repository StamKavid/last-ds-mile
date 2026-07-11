"""seal(): the human's one signature — split, lock the labels, write the Contract."""
from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from sealed_bet.contract import Contract
from sealed_bet.ledger import write_header
from sealed_bet.metrics import baseline_score
from sealed_bet.splits import split
from sealed_bet.state import init_state


def _hash(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def seal(data_path: str, target: str, task: str, metric: str, out_dir: str,
         strategy: str = "random", group_key=None, time_col=None,
         held_frac: float = 0.2, seed: int = 0, input_mode: str = "full",
         ledger_path: str = "LEDGER.md") -> Contract:
    out = Path(out_dir)
    init_state(out)  # guard first: refuse re-sealing an opened project before anything else touches disk

    df = pd.read_csv(data_path)
    dev, held = split(df, strategy=strategy, seed=seed, held_frac=held_frac,
                      group_key=group_key, time_col=time_col)

    base = baseline_score(dev[target].to_numpy(), held[target].to_numpy(), metric)
    contract = Contract(
        target=target, task=task, metric=metric,
        split={"strategy": strategy, "group_key": group_key, "time_col": time_col},
        baseline_score=base, held_frac=held_frac, seed=seed, data_hash=_hash(data_path),
        input_mode=input_mode,
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    ).validate()

    (out / "held").mkdir(parents=True, exist_ok=True)
    dev.to_csv(out / "dev.csv", index=False)
    held.drop(columns=[target]).to_csv(out / "held" / "features.csv", index=False)
    held[[target]].to_csv(out / "held" / "_sealed_target.csv", index=False)
    contract.save(out / "contract.json")
    write_header(ledger_path, contract)
    return contract


def main() -> None:
    ap = argparse.ArgumentParser(prog="sealed_bet.seal")
    ap.add_argument("--data", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--task", required=True, choices=["regression", "classification"])
    ap.add_argument("--metric", required=True)
    ap.add_argument("--out", default=".last-ds-mile")
    ap.add_argument("--strategy", default="random", choices=["random", "group", "time"])
    ap.add_argument("--group-key", default=None)
    ap.add_argument("--time-col", default=None)
    ap.add_argument("--held-frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--ledger", default="LEDGER.md")
    a = ap.parse_args()
    c = seal(a.data, a.target, a.task, a.metric, a.out, a.strategy, a.group_key,
             a.time_col, a.held_frac, a.seed, "full", a.ledger)
    print(f"Sealed. baseline_score={c.baseline_score:.4f}. Build in the open; open once with score.py.")


if __name__ == "__main__":
    main()
