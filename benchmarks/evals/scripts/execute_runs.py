#!/usr/bin/env python3
"""Run the executor agent over workspaces that run_eval.py scaffolded.

`run_eval.py` deliberately stops at scaffolding — it builds the workspaces and
prints what to do. This is the other half: it walks those workspaces and invokes
`claude -p` in each, saving the JSONL transcript beside the prompt.

THIS SPENDS MONEY. It prints a cost estimate from each eval's `max_cost_usd`
budget and requires explicit confirmation before the first run. `--dry-run`
prints the plan and exits.

The two arms differ only in whether the plugin is loaded:

    with_skill     runs with the repo passed via --plugin-dir, so the /ds-* skills
                   are discoverable.
    without_skill  runs with no plugin argument at all.

Either way the workspace sits outside the repository, so neither arm inherits the
project's CLAUDE.md. How the arm was configured is written into
`eval_metadata.json` under `environment.plugin_disabled_how`, because an
unrecorded arm toggle is why iteration-2's baseline cannot be trusted.

Usage:
    python execute_runs.py --results-root <root> --dry-run
    python execute_runs.py --results-root <root>
    python execute_runs.py --results-root <root> --only-arm with_skill
"""
import argparse
import datetime as dt
import json
import pathlib
import shutil
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def iter_workspaces(root: pathlib.Path, only_arm: str | None):
    for meta_path in sorted(root.glob("eval-*/*/trial-*/eval_metadata.json")):
        with meta_path.open(encoding="utf-8") as fh:
            meta = json.load(fh)
        if only_arm and meta["arm"] != only_arm:
            continue
        yield meta_path.parent, meta


def build_command(workspace: pathlib.Path, meta: dict, claude_bin: str) -> list[str]:
    cmd = [
        claude_bin,
        "-p", meta["prompt"],
        "--output-format", "stream-json",
        "--verbose",
        "--permission-mode", "acceptEdits",
    ]
    if meta["arm"] == "with_skill":
        cmd += ["--plugin-dir", str(REPO_ROOT)]
    return cmd


def run_one(workspace: pathlib.Path, meta: dict, claude_bin: str, timeout_s: int) -> dict:
    outputs = workspace / "outputs"
    outputs.mkdir(exist_ok=True)
    transcript = workspace / "transcript.jsonl"
    stderr_log = workspace / "stderr.log"
    cmd = build_command(workspace, meta, claude_bin)

    started = dt.datetime.now(dt.timezone.utc)
    try:
        with transcript.open("w", encoding="utf-8") as out, \
             stderr_log.open("w", encoding="utf-8") as err:
            proc = subprocess.run(
                cmd, cwd=outputs, stdout=out, stderr=err,
                timeout=timeout_s, text=True,
            )
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        exit_code = -1
        stderr_log.write_text(
            f"TIMEOUT after {timeout_s}s\n", encoding="utf-8")

    (workspace / "exit_code.txt").write_text(str(exit_code), encoding="utf-8")

    # Record how this arm was actually configured. Without it a surprising
    # result cannot be separated from a misconfigured run.
    meta.setdefault("environment", {})["plugin_disabled_how"] = (
        "n/a — plugin loaded via --plugin-dir" if meta["arm"] == "with_skill"
        else "no --plugin-dir passed; plugin not on the command line"
    )
    meta["environment"]["executor_command"] = [
        c if c != meta["prompt"] else "<prompt.md>" for c in cmd
    ]
    meta["environment"]["started_at"] = started.isoformat()
    meta["environment"]["exit_code"] = exit_code
    (workspace / "eval_metadata.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8")

    return {"exit_code": exit_code, "transcript_bytes": transcript.stat().st_size
            if transcript.exists() else 0}


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results-root", required=True,
                    help="the iteration-N directory run_eval.py scaffolded")
    ap.add_argument("--only-arm", choices=["with_skill", "without_skill"])
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan and the cost estimate, run nothing")
    ap.add_argument("--timeout", type=int, default=1800,
                    help="per-run timeout in seconds (default 1800)")
    ap.add_argument("--claude-bin", default=shutil.which("claude") or "claude")
    ap.add_argument("--yes", action="store_true",
                    help="skip the confirmation prompt (for unattended runs)")
    args = ap.parse_args()

    root = pathlib.Path(args.results_root).resolve()
    if not root.exists():
        sys.exit(f"results root not found: {root}")

    planned = list(iter_workspaces(root, args.only_arm))
    if not planned:
        sys.exit(f"no workspaces under {root}"
                 + (f" for arm {args.only_arm}" if args.only_arm else ""))

    budget = sum(m.get("max_cost_usd") or 0.0 for _, m in planned)
    print(f"{len(planned)} run(s) under {root}")
    for workspace, meta in planned:
        print(f"  eval-{meta['eval_id']} {meta['arm']:<14} trial-{meta['trial']}  "
              f"budget ${meta.get('max_cost_usd', 0):.2f}  "
              f"{workspace.relative_to(root)}")
    print(f"\nBudgeted total: ~${budget:.2f} (per-case max_cost_usd, not a hard cap —"
          f" nothing kills a run mid-flight)")
    print(f"Executor: {args.claude_bin}")

    if args.dry_run:
        print("\n--dry-run: nothing executed.")
        return 0

    if not args.yes:
        reply = input(f"\nSpend up to ~${budget:.2f} running these? [y/N] ").strip().lower()
        if reply not in ("y", "yes"):
            print("aborted.")
            return 1

    failures = 0
    for i, (workspace, meta) in enumerate(planned, 1):
        label = f"eval-{meta['eval_id']} {meta['arm']} trial-{meta['trial']}"
        print(f"\n[{i}/{len(planned)}] {label} ...", flush=True)
        result = run_one(workspace, meta, args.claude_bin, args.timeout)
        status = "ok" if result["exit_code"] == 0 else f"exit {result['exit_code']}"
        print(f"    {status}, transcript {result['transcript_bytes'] / 1024:.0f} KB")
        if result["exit_code"] != 0:
            failures += 1

    print(f"\nDone. {len(planned) - failures} ok, {failures} failed.")
    print("\nNext:")
    print(f"  python benchmarks/evals/scripts/grade_manifest.py build --results-root {root}")
    print("  # grade each dir under _blind/ against agents/grader.md -> grading.json")
    print(f"  python benchmarks/evals/scripts/grade_manifest.py unblind --results-root {root}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
