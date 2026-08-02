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
import statistics
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


def _trial_usage(trial_dir):
    """Pull cost/latency/turns/cache-read tokens from a trial's transcript.jsonl.

    Reads the harness's own `result` record (last line of that type) rather than
    re-deriving anything — total_cost_usd and duration_ms are what the harness itself
    billed and measured. Returns None if no transcript or no result record exists (e.g.
    a scaffolded-but-not-yet-run trial), so partial result sets don't crash aggregation.
    """
    tp = trial_dir / "transcript.jsonl"
    if not tp.exists():
        return None
    result = None
    try:
        with tp.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") == "result":
                    result = obj
    except OSError:
        return None
    if result is None:
        return None
    usage = result.get("usage") or {}
    return {
        "cost_usd": result.get("total_cost_usd"),
        "duration_s": (result.get("duration_ms") or 0) / 1000.0,
        "turns": result.get("num_turns"),
        "cache_read_tokens": usage.get("cache_read_input_tokens"),
        "output_tokens": usage.get("output_tokens"),
    }


def collect_costs(results_root):
    """Return {eval_id: {arm: [per-trial usage dicts]}}, skipping trials with no
    transcript (ungraded/unscaffolded) rather than failing the whole run."""
    costs = collections.defaultdict(lambda: collections.defaultdict(list))
    for trial_dir in sorted(results_root.glob("eval-*/*/trial-*")):
        arm = trial_dir.parent.name
        eid_str = trial_dir.parent.parent.name.split("-", 1)[-1]
        try:
            eid = int(eid_str)
        except ValueError:
            continue
        usage = _trial_usage(trial_dir)
        if usage is not None:
            costs[eid][arm].append(usage)
    return costs


def cost_summary(costs):
    """Per-eval and overall cost/latency stats per arm, plus a with_skill/without_skill
    ratio and an explicit budget check (with_skill mean cost should stay within 2x)."""
    per_eval = []
    overall = {"with_skill": {"cost_usd": [], "duration_s": [], "turns": []},
               "without_skill": {"cost_usd": [], "duration_s": [], "turns": []}}

    for eid in sorted(costs):
        row = {"eval_id": eid}
        for arm in ("with_skill", "without_skill"):
            trials = costs[eid].get(arm, [])
            cost_vals = [t["cost_usd"] for t in trials if t["cost_usd"] is not None]
            dur_vals = [t["duration_s"] for t in trials if t["duration_s"] is not None]
            turn_vals = [t["turns"] for t in trials if t["turns"] is not None]
            row[arm] = {
                "cost_usd": _stats(cost_vals),
                "duration_s": _stats(dur_vals),
                "turns": _stats(turn_vals),
                "trials": len(trials),
            }
            overall[arm]["cost_usd"].extend(cost_vals)
            overall[arm]["duration_s"].extend(dur_vals)
            overall[arm]["turns"].extend(turn_vals)
        per_eval.append(row)

    overall_row = {}
    for arm in ("with_skill", "without_skill"):
        overall_row[arm] = {
            "cost_usd": _stats(overall[arm]["cost_usd"]),
            "duration_s": _stats(overall[arm]["duration_s"]),
            "turns": _stats(overall[arm]["turns"]),
        }

    ws_cost = (overall_row["with_skill"]["cost_usd"] or {}).get("mean")
    wo_cost = (overall_row["without_skill"]["cost_usd"] or {}).get("mean")
    budget = {"limit_multiplier": 2.0}
    if ws_cost is not None and wo_cost is not None and wo_cost > 0:
        ratio = round(ws_cost / wo_cost, 3)
        budget["with_skill_mean_usd"] = ws_cost
        budget["without_skill_mean_usd"] = wo_cost
        budget["ratio"] = ratio
        budget["within_budget"] = ratio <= budget["limit_multiplier"]
    else:
        budget["ratio"] = None
        budget["within_budget"] = None

    overall_row["budget_check"] = budget
    return per_eval, overall_row


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


def markdown(per_case, run_summary, cost_per_eval, cost_overall):
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

    if cost_overall:
        lines.append("")
        lines.append("## Cost & latency by case")
        lines.append("")
        lines.append("| eval | with_skill $ | without_skill $ | with_skill turns | without_skill turns |")
        lines.append("|---|---|---|---|---|")
        for row in cost_per_eval:
            ws_c = (row["with_skill"]["cost_usd"] or {}).get("mean")
            wo_c = (row["without_skill"]["cost_usd"] or {}).get("mean")
            ws_t = (row["with_skill"]["turns"] or {}).get("mean")
            wo_t = (row["without_skill"]["turns"] or {}).get("mean")
            lines.append(f"| {row['eval_id']} | {ws_c} | {wo_c} | {ws_t} | {wo_t} |")
        lines.append("")
        budget = cost_overall.get("budget_check", {})
        ws_mean = budget.get("with_skill_mean_usd")
        wo_mean = budget.get("without_skill_mean_usd")
        ratio = budget.get("ratio")
        within = budget.get("within_budget")
        if ratio is not None:
            verdict = "within" if within else "OVER"
            lines.append(f"**Overall mean cost — with_skill ${ws_mean} vs without_skill ${wo_mean} "
                         f"({ratio}x, {verdict} the {budget['limit_multiplier']}x budget).**")
        lines.append("")
        lines.append("Cost/latency come from each trial's own harness `result` record "
                     "(total_cost_usd, duration_ms, num_turns) — not re-derived. The budget check "
                     "flags whether with_skill's mean cost stays within the stated ceiling relative "
                     "to without_skill; a plugin that wins on pass^k but blows the budget has not "
                     "actually proven its value.")

    return "\n".join(lines) + "\n"


def load_eval_names(dataset):
    """Map {eval_id: eval_name} from the dataset's evals.json, if present."""
    p = EVALS_DIR / dataset / "evals.json"
    if not p.exists():
        return {}
    spec = json.load(p.open(encoding="utf-8"))
    return {e["id"]: e.get("gate_under_test", f"eval-{e['id']}") for e in spec["evals"]}


def _stats(values):
    if not values:
        return None
    return {
        "mean": round(statistics.fmean(values), 4),
        "stddev": round(statistics.pstdev(values), 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def skill_creator_benchmark(results_root, names, skill_name):
    """Emit skill-creator's exact benchmark.json schema (its eval-viewer reads these
    field names verbatim: runs[].configuration, runs[].result.pass_rate,
    run_summary.<config>.pass_rate.{mean,stddev}). Timing/token fields are populated
    from each trial's transcript.jsonl `result` record when present, null otherwise
    (e.g. a graded run whose transcript wasn't kept)."""
    runs = []
    by_cfg = collections.defaultdict(list)
    time_by_cfg = collections.defaultdict(list)
    tokens_by_cfg = collections.defaultdict(list)
    eval_ids = set()
    for gf in sorted(results_root.glob("eval-*/*/trial-*/grading.json")):
        g = json.load(gf.open(encoding="utf-8"))
        cfg = gf.parent.parent.name              # with_skill / without_skill
        run_number = int(gf.parent.name.split("-")[-1])
        s = g.get("summary") or {}
        exps = g.get("expectations", [])
        passed = s.get("passed", sum(1 for e in exps if e["passed"]))
        total = s.get("total", len(exps))
        pr = s.get("pass_rate", round(passed / total, 4) if total else 0.0)
        eid = g["eval_id"]
        eval_ids.add(eid)
        by_cfg[cfg].append(pr)
        notes = g.get("notes", "")

        usage = _trial_usage(gf.parent)
        time_s = usage["duration_s"] if usage else None
        tokens = (usage["cache_read_tokens"] or 0) + (usage["output_tokens"] or 0) if usage else None
        if time_s is not None:
            time_by_cfg[cfg].append(time_s)
        if tokens is not None:
            tokens_by_cfg[cfg].append(tokens)

        runs.append({
            "eval_id": eid,
            "eval_name": names.get(eid, f"eval-{eid}"),
            "configuration": cfg,
            "run_number": run_number,
            "result": {
                "pass_rate": pr, "passed": passed,
                "failed": total - passed, "total": total,
                "time_seconds": round(time_s, 1) if time_s is not None else None,
                "tokens": tokens, "tool_calls": None, "errors": None,
            },
            "expectations": exps,
            "notes": [notes] if notes else [],
        })

    run_summary = {}
    for cfg in ("with_skill", "without_skill"):
        run_summary[cfg] = {
            "pass_rate": _stats(by_cfg.get(cfg, [])),
            "time_seconds": _stats(time_by_cfg.get(cfg, [])),
            "tokens": _stats(tokens_by_cfg.get(cfg, [])),
        }
    mw = (run_summary["with_skill"]["pass_rate"] or {}).get("mean")
    mo = (run_summary["without_skill"]["pass_rate"] or {}).get("mean")
    if mw is not None and mo is not None:
        run_summary["delta"] = {"pass_rate": f"{mw - mo:+.2f}"}

    return {
        "metadata": {
            "skill_name": skill_name,
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "evals_run": sorted(eval_ids),
            "runs_per_configuration": max((len(v) for v in by_cfg.values()), default=0),
        },
        "runs": sorted(runs, key=lambda r: (r["eval_id"], r["configuration"], r["run_number"])),
        "run_summary": run_summary,
        "notes": [],
    }


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
    costs = collect_costs(results_root)
    cost_per_eval, cost_overall = cost_summary(costs)

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
        "cost": {
            "per_eval": cost_per_eval,
            "overall": cost_overall,
        },
        "notes": "",
    }
    bench_path = results_root / "benchmark.json"
    bench_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    summary_path = results_root / "summary.md"
    summary_path.write_text(markdown(per_case, run_summary, cost_per_eval, cost_overall), encoding="utf-8")

    # Also emit skill-creator's exact schema, for their eval-viewer.
    sc = skill_creator_benchmark(results_root, load_eval_names(args.dataset), out["metadata"]["skill_name"])
    sc_path = results_root / "benchmark.skill-creator.json"
    sc_path.write_text(json.dumps(sc, indent=2), encoding="utf-8")

    print(f"wrote {bench_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {sc_path}  (skill-creator eval-viewer schema)")
    print(f"\noverall pass^k — with_skill {run_summary.get('with_skill')} "
          f"vs without_skill {run_summary.get('without_skill')} (gap {run_summary.get('gap')})")

    budget = cost_overall.get("budget_check", {})
    if budget.get("ratio") is not None:
        verdict = "within" if budget["within_budget"] else "OVER"
        print(f"cost budget — with_skill ${budget['with_skill_mean_usd']} vs "
              f"without_skill ${budget['without_skill_mean_usd']} "
              f"({budget['ratio']}x, {verdict} the {budget['limit_multiplier']}x ceiling)")


if __name__ == "__main__":
    main()
