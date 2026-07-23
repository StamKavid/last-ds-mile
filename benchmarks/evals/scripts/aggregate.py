#!/usr/bin/env python3
"""Aggregate per-run grading.json files into benchmark.json + a markdown summary.

Computes, per expectation and per arm:
  pass^k (pass_hat_k) — passed in ALL k trials (consistency, practice #7)
  pass@k (pass_at_k)  — passed in AT LEAST ONE trial (peak luck, practice #7)
and the with_skill - without_skill gap (marginal reproducible value; a ~0 gap on a
passing expectation is a retirement signal, practice #10).

Reads the results tree produced by run_eval.py:
    results/iteration-N/eval-<id>/<arm>/trial-<t>/grading.json

stdlib-only. Usage:
    python aggregate.py credit-card-fraud --iteration 1
"""
import argparse
import collections
import datetime as dt
import json
import pathlib
import sys

EVALS_DIR = pathlib.Path(__file__).resolve().parents[1]


def collect(results_root):
    """Return {eval_id: {arm: {expectation_text: [bool per trial]}}}."""
    data = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(list)))
    grading_files = sorted(results_root.glob("eval-*/*/trial-*/grading.json"))
    if not grading_files:
        sys.exit(f"no grading.json found under {results_root} — grade the runs first")
    for gf in grading_files:
        arm = gf.parent.parent.name
        with gf.open(encoding="utf-8") as fh:
            grading = json.load(fh)
        eid = grading.get("eval_id")
        for exp in grading.get("expectations", []):
            data[eid][arm][exp["text"]].append(bool(exp["passed"]))
    return data


def summarize(data):
    per_expectation = []
    per_case = []
    arm_totals = collections.defaultdict(lambda: [0, 0])  # arm -> [pass^k count, expectation count]

    for eid in sorted(data):
        arms = data[eid]
        texts = sorted({t for arm in arms.values() for t in arm})
        case_pass = collections.defaultdict(lambda: [0, 0])
        for text in texts:
            row = {"eval_id": eid, "text": text}
            hats = {}
            for arm in ("with_skill", "without_skill"):
                trials = arms.get(arm, {}).get(text, [])
                n = len(trials)
                pass_hat = float(all(trials)) if n else 0.0
                pass_at = float(any(trials)) if n else 0.0
                row[arm] = {
                    "pass_hat_k": pass_hat,
                    "pass_at_k": pass_at,
                    "passes": sum(trials),
                    "trials": n,
                }
                hats[arm] = pass_hat
                if n:
                    case_pass[arm][0] += pass_hat
                    case_pass[arm][1] += 1
                    arm_totals[arm][0] += pass_hat
                    arm_totals[arm][1] += 1
            row["gap"] = round(hats.get("with_skill", 0.0) - hats.get("without_skill", 0.0), 3)
            per_expectation.append(row)

        case_row = {"eval_id": eid}
        for arm in ("with_skill", "without_skill"):
            c, tot = case_pass[arm]
            case_row[f"{arm}_pass_rate"] = round(c / tot, 3) if tot else None
        per_case.append(case_row)

    run_summary = {}
    for arm in ("with_skill", "without_skill"):
        c, tot = arm_totals[arm]
        run_summary[arm] = round(c / tot, 3) if tot else None
    if run_summary["with_skill"] is not None and run_summary["without_skill"] is not None:
        run_summary["gap"] = round(run_summary["with_skill"] - run_summary["without_skill"], 3)
    return per_expectation, per_case, run_summary


def markdown(per_case, run_summary, trials_hint):
    lines = ["# Benchmark summary — pass^k by case", ""]
    lines.append("| eval | with_skill pass^k | without_skill pass^k |")
    lines.append("|---|---|---|")
    for c in per_case:
        lines.append(f"| {c['eval_id']} | {c['with_skill_pass_rate']} | {c['without_skill_pass_rate']} |")
    lines.append("")
    ws, wo = run_summary.get("with_skill"), run_summary.get("without_skill")
    lines.append(f"**Overall pass^k — with_skill {ws} vs without_skill {wo} (gap {run_summary.get('gap')}).**")
    lines.append("")
    lines.append("pass^k = fraction of expectations that passed in *all* trials of that arm. "
                 "A large gap is the plugin's reproducible marginal value; a gap near zero on "
                 "passing expectations means the base model already does it (retire, practice #10).")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset", help="dataset dir under benchmarks/evals/ (e.g. credit-card-fraud)")
    ap.add_argument("--iteration", type=int, default=1)
    ap.add_argument("--root", help="explicit results root (dir containing eval-*/); "
                                   "overrides the default results/iteration-N/ path. "
                                   "Use for the committed example tree.")
    args = ap.parse_args()

    if args.root:
        results_root = pathlib.Path(args.root)
        if not results_root.is_absolute() and not results_root.exists():
            results_root = EVALS_DIR / args.root
    else:
        results_root = EVALS_DIR / args.dataset / "results" / f"iteration-{args.iteration}"
    if not results_root.exists():
        sys.exit(f"no results at {results_root}")

    data = collect(results_root)
    per_expectation, per_case, run_summary = summarize(data)

    out = {
        "metadata": {
            "skill_name": "last-ds-mile",
            "dataset": args.dataset,
            "iteration": args.iteration,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        },
        "per_expectation": per_expectation,
        "per_case": per_case,
        "run_summary": run_summary,
        "notes": "",
    }
    bench_path = results_root / "benchmark.json"
    bench_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    summary_path = results_root / "summary.md"
    summary_path.write_text(markdown(per_case, run_summary, None), encoding="utf-8")
    print(f"wrote {bench_path}")
    print(f"wrote {summary_path}")
    print(f"\noverall pass^k — with_skill {run_summary.get('with_skill')} "
          f"vs without_skill {run_summary.get('without_skill')} (gap {run_summary.get('gap')})")


if __name__ == "__main__":
    main()
