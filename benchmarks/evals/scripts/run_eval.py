#!/usr/bin/env python3
"""Scaffold isolated workspaces for one with/without benchmark.

This script does NOT invoke an agent — agent invocation is harness-specific and
usually interactive. It materializes, for every {eval_id, arm, trial}, a clean
workspace (practice #6: isolate each run) containing a copy of the dataset, the
prompt, and an eval_metadata.json, then prints the exact command to run in each
one. You run the agent in each workspace, drop its transcript + outputs there,
then grade with agents/grader.md and aggregate with aggregate.py.

stdlib-only, no third-party deps. Usage:

    python run_eval.py credit-card-fraud/evals.json --trials 5 --harness claude-code
    python run_eval.py credit-card-fraud/evals.json --arm without_skill --trials 5
"""
import argparse
import datetime as dt
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
EVALS_DIR = pathlib.Path(__file__).resolve().parents[1]


def load_evals(evals_path: pathlib.Path) -> dict:
    with evals_path.open(encoding="utf-8") as fh:
        return json.load(fh)


def workspace_for(results_root, eval_id, arm, trial):
    return results_root / f"eval-{eval_id}" / arm / f"trial-{trial}"


def scaffold(evals_path, trials, arms, harness, iteration):
    spec = load_evals(evals_path)
    dataset_path = REPO_ROOT / spec["dataset"]["path"]
    if not dataset_path.exists():
        sys.exit(f"dataset not found: {dataset_path}")

    results_root = evals_path.parent / "results" / f"iteration-{iteration}"
    made = []
    for ev in spec["evals"]:
        for arm in arms:
            for trial in range(1, trials + 1):
                ws = workspace_for(results_root, ev["id"], arm, trial)
                (ws / "outputs").mkdir(parents=True, exist_ok=True)
                # The dataset is read-only shared input, referenced by path — not copied
                # (a 150MB CSV x dozens of runs is pointless). Isolation (practice #6) is
                # about the mutable workspace: each run writes only into its own outputs/.
                # A run that MODIFIES the data must copy it into outputs/ itself first.
                (ws / "prompt.md").write_text(ev["prompt"] + "\n", encoding="utf-8")
                meta = {
                    "eval_id": ev["id"],
                    "arm": arm,
                    "trial": trial,
                    "prompt": ev["prompt"],
                    "dataset_path": str(dataset_path),
                    "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "harness": harness,
                }
                (ws / "eval_metadata.json").write_text(
                    json.dumps(meta, indent=2), encoding="utf-8"
                )
                made.append((ev["id"], arm, trial, ws))

    print(f"Scaffolded {len(made)} workspaces under {results_root}\n")
    print("For each workspace: run the executor agent with cwd = the outputs/ dir,")
    print("feeding it prompt.md. Save the transcript to transcript.md in the workspace.")
    print(f"\n  with_skill arm : {spec['arms']['with_skill']}")
    print(f"  without_skill  : {spec['arms']['without_skill']}\n")
    print("Then grade each run against agents/grader.md, writing grading.json next to")
    print("its transcript, and run aggregate.py to compute pass^k and the arm gap.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evals_json", help="path to an evals.json (relative to benchmarks/evals/ ok)")
    ap.add_argument("--trials", type=int, default=5, help="trials per case per arm (practice #7)")
    ap.add_argument("--arm", choices=["with_skill", "without_skill"], action="append",
                    help="limit to one arm; repeatable. Default: both.")
    ap.add_argument("--harness", default="claude-code",
                    help="label recorded in metadata (practice #8: eval per target harness)")
    ap.add_argument("--iteration", type=int, default=1)
    args = ap.parse_args()

    evals_path = pathlib.Path(args.evals_json)
    if not evals_path.is_absolute() and not evals_path.exists():
        evals_path = EVALS_DIR / args.evals_json
    if not evals_path.exists():
        sys.exit(f"evals.json not found: {args.evals_json}")

    arms = args.arm or ["with_skill", "without_skill"]
    scaffold(evals_path, args.trials, arms, args.harness, args.iteration)


if __name__ == "__main__":
    main()
