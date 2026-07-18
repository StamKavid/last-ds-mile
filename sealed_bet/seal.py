"""seal(): the human's one signature — split, lock the labels, write the Contract."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from sealed_bet.adversary import leakage_adversary, split_adversary
from sealed_bet.auto import ceiling_baseline
from sealed_bet.contract import Contract
from sealed_bet.ledger import append_leakage_probe, append_probe, append_probe_na, write_header
from sealed_bet.metrics import METRICS, baseline_predict
from sealed_bet.splits import auto_stratify_col, split
from sealed_bet.state import init_state


def _hash(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def load_baseline_fn(spec: str):
    """Load a baseline callable from a 'path/to/file.py:function_name' spec.

    The function receives (dev_df, held_features_df) and returns one prediction
    per held row. This is how /ds-baseline's chosen heuristic -- the
    neighbourhood $/sqft lookup, the 'target every month-to-month customer'
    rule -- becomes an executable rival to the model rather than a paragraph
    of prose that never gets scored.
    """
    if ":" not in spec:
        raise ValueError(
            f"--baseline-py must look like 'path/to/file.py:function_name', got {spec!r}"
        )
    path_str, fn_name = spec.rsplit(":", 1)
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"baseline module not found: {path}")
    mod_spec = importlib.util.spec_from_file_location(path.stem, path)
    if mod_spec is None or mod_spec.loader is None:
        raise ImportError(f"could not load baseline module from {path}")
    module = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(module)
    if not hasattr(module, fn_name):
        raise AttributeError(f"{path} has no function named {fn_name!r}")
    return getattr(module, fn_name)


def seal(data_path: str, target: str, task: str, metric: str, out_dir: str,
         strategy: str = "random", group_key=None, time_col=None,
         held_frac: float = 0.2, seed: int = 0, input_mode: str = "full",
         ledger_path: str = "LEDGER.md", budget: int = 15,
         ceiling_estimate: float | None = None, baseline_fn=None,
         exclude_from_features: list[str] | None = None) -> Contract:
    out = Path(out_dir)
    init_state(out)  # guard first: refuse re-sealing an opened project before anything else touches disk

    df = pd.read_csv(data_path)
    dev, held = split(df, strategy=strategy, seed=seed, held_frac=held_frac,
                      group_key=group_key, time_col=time_col,
                      stratify_col=auto_stratify_col(task, strategy, target))

    excluded = exclude_from_features or []
    if excluded:
        # Drop these from the frames themselves -- not just from feature_cols
        # below -- so an excluded column (e.g. a raw future-looking time_col
        # with no standalone predictive legitimacy) can never leak into
        # modeling regardless of how a downstream caller re-derives its own
        # feature list from dev.csv's columns (as /ds-auto's loop does). This
        # is the fix for the gap house-prices' 05-validate.md found: seal()
        # used to have no way to split by a time_col while also keeping it out
        # of the model's own inputs.
        dev = dev.drop(columns=excluded)
        held = held.drop(columns=excluded)

    feature_cols = [c for c in dev.columns if c != target]
    held_features = held.drop(columns=[target])
    m = METRICS[metric]
    if baseline_fn is None:
        base_preds = baseline_predict(dev[target].to_numpy(), len(held), metric)
        baseline_kind = "constant"
    else:
        base_preds = np.asarray(baseline_fn(dev, held_features))
        if len(base_preds) != len(held):
            raise ValueError(
                f"baseline_fn returned {len(base_preds)} predictions for {len(held)} "
                f"held rows — it must return exactly one prediction per held row, in "
                f"the same order as held/features.csv"
            )
        if not np.all(np.isfinite(base_preds)):
            raise ValueError(
                "baseline_fn returned non-finite predictions (NaN/inf); a baseline "
                "must produce a real prediction for every held row — decide explicitly "
                "what it should fall back to for rows its rule doesn't cover"
            )
        baseline_kind = "heuristic"
    base = float(m.fn(held[target].to_numpy(), base_preds))
    ceiling = ceiling_baseline(dev, target, feature_cols, task, metric,
                              human_estimate=ceiling_estimate, seed=seed,
                              model_dir=str(out / "auto" / "ceiling"))
    contract = Contract(
        target=target, task=task, metric=metric,
        split={"strategy": strategy, "group_key": group_key, "time_col": time_col},
        baseline_score=base, baseline_kind=baseline_kind, held_frac=held_frac, seed=seed,
        data_hash=_hash(data_path), input_mode=input_mode,
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        budget=budget, ceiling_score=ceiling["score"], ceiling_source=ceiling["source"],
        excluded_features=excluded,
    ).validate()

    (out / "held").mkdir(parents=True, exist_ok=True)
    dev.to_csv(out / "dev.csv", index=False)
    held_features.to_csv(out / "held" / "features.csv", index=False)
    held[[target]].to_csv(out / "held" / "_sealed_target.csv", index=False)
    # Sealed alongside the labels (the `_sealed*` prefix is what seal_guard blocks):
    # open_seal needs the baseline's PER-ROW predictions, not just its scalar score,
    # to compute the paired σ. Sealing them keeps the agent from reverse-engineering
    # held rows from a readable baseline-prediction vector.
    pd.DataFrame({"baseline_pred": base_preds}).to_csv(
        out / "held" / "_sealed_baseline_preds.csv", index=False
    )
    contract.save(out / "contract.json")
    write_header(ledger_path, contract)
    if strategy == "time":
        # split_adversary certifies dev/held are statistically indistinguishable --
        # the right check for a random/group split, but the WRONG check for a time
        # split: dev and held are supposed to look different there (held is always
        # strictly later), so it would reliably report a false-positive "SUSPECT"
        # (discovered running this exact code against the house-prices benchmark;
        # see BENCHMARKS.md). Skip it outright rather than compute and log a verdict
        # that doesn't mean what its own wording claims.
        append_probe_na(ledger_path, "strategy=\"time\" — dev/held are supposed to be "
                                     "distinguishable here (held is always later); this "
                                     "probe only certifies random/group splits")
    else:
        _run_probe(
            ledger_path, "split-adversary",
            lambda: split_adversary(dev, held_features, feature_cols, seed=seed),
            lambda r: append_probe(ledger_path, r["auc"], r["sigma"], r["lift"], r["certified"]),
        )
    _run_probe(
        ledger_path, "leakage-adversary",
        lambda: leakage_adversary(dev, target, feature_cols, task, seed=seed),
        lambda r: append_leakage_probe(ledger_path, r),
    )
    return contract


def _run_probe(ledger_path: str, name: str, run, report) -> None:
    """Run one warn-only probe: never let a diagnostic failure fail the seal."""
    try:
        report(run())
    except Exception as exc:
        try:
            with open(ledger_path, "a", encoding="utf-8") as f:
                f.write(f"\n## Probe ({name}, warn-only)\n- probe skipped: {exc}\n")
        except Exception:  # even logging the failure must never fail the seal
            pass


def main() -> None:
    # See sealed_bet.score.main's identical guard: a non-UTF-8 Windows console
    # (cp1252, the default) crashes on non-ASCII output otherwise.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
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
    ap.add_argument("--budget", type=int, default=15)
    ap.add_argument("--ceiling-estimate", type=float, default=None)
    ap.add_argument(
        "--baseline-py", default=None,
        help="'path/to/file.py:function_name' — a non-ML heuristic taking "
             "(dev_df, held_features_df) and returning one prediction per held row. "
             "Without this the baseline is a constant, which for roc_auc scores "
             "exactly 0.5 on every dataset and is a floor, not a rival.",
    )
    ap.add_argument(
        "--exclude-from-features", default=None,
        help="comma-separated column names to keep out of the model's feature set "
             "entirely (e.g. a time_col with no standalone predictive legitimacy) "
             "while still using them to build the split.",
    )
    a = ap.parse_args()
    baseline_fn = load_baseline_fn(a.baseline_py) if a.baseline_py else None
    exclude = [c.strip() for c in a.exclude_from_features.split(",")] if a.exclude_from_features else None
    c = seal(a.data, a.target, a.task, a.metric, a.out, a.strategy, a.group_key,
             a.time_col, a.held_frac, a.seed, "full", a.ledger, a.budget,
             a.ceiling_estimate, baseline_fn, exclude)
    print(f"Sealed. baseline_score={c.baseline_score:.4f} ({c.baseline_kind}) "
          f"ceiling_score={c.ceiling_score:.4f} ({c.ceiling_source}). "
          f"Build in the open; open once with score.py.")


if __name__ == "__main__":
    main()
