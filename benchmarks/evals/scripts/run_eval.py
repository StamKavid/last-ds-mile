#!/usr/bin/env python3
"""Scaffold isolated workspaces for one with/without behavioral benchmark.

This script does NOT invoke an agent — agent invocation is harness-specific and
usually interactive. It materializes, for every {eval_id, arm, trial}, a clean
workspace containing the prompt, the dataset, and an eval_metadata.json recording
the environment the run will see, then prints the exact command to run in each
one. You run the agent in each workspace, drop its transcript + outputs there,
then grade with agents/grader.md and aggregate with aggregate.py.

ISOLATION. Workspaces default to a temp directory
OUTSIDE this repository. Iteration-2 scaffolded into
`benchmarks/evals/<dataset>/results/`, which sits under this repo's own
CLAUDE.md — a file that states the pipeline's hard-gate doctrine verbatim. Both
arms inherited it, so the `without_skill` arm was not a clean baseline, and the
transcripts do not record enough to prove otherwise either way. Graded results are
copied back into the repo afterwards; the dataset never is.

stdlib-only, no third-party deps. Usage:

    python run_eval.py credit-card-fraud/evals.json --trials 5 --iteration 3
    python run_eval.py credit-card-fraud/evals.json --arm without_skill --trials 5
    python run_eval.py credit-card-fraud/evals.json --evals 3 4 6 --trials 2 \
        --arm with_skill                       # the cheap negative-trigger smoke subset
    python run_eval.py credit-card-fraud/evals.json --workspace-root /some/scratch
"""
import argparse
import datetime as dt
import functools
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
EVALS_DIR = pathlib.Path(__file__).resolve().parents[1]


def load_evals(evals_path: pathlib.Path) -> dict:
    with evals_path.open(encoding="utf-8") as fh:
        return json.load(fh)


@functools.lru_cache(maxsize=None)
def _environment(arm: str) -> tuple:
    """Cached inner form of capture_environment, as a hashable tuple.

    Iteration-2's metadata recorded only `arm: with_skill`, with nothing about how
    the plugin was enabled or disabled and nothing about ambient context. When the
    numbers came out wrong there was no way to rule the environment in or out.
    """
    env = {
        "arm": arm,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "model_env": os.environ.get("ANTHROPIC_MODEL") or os.environ.get("CLAUDE_MODEL"),
        "settings_env": os.environ.get("CLAUDE_SETTINGS"),
        "installed_plugins": None,
        "installed_plugins_source": None,
        "git_commit": None,
        "plugin_disabled_how": None if arm == "with_skill" else "RECORD THIS MANUALLY",
    }
    try:
        env["git_commit"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
            capture_output=True, text=True, timeout=10,
        ).stdout.strip() or None
    except Exception:
        pass

    manifest = pathlib.Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    if manifest.exists():
        try:
            with manifest.open(encoding="utf-8") as fh:
                env["installed_plugins"] = sorted(json.load(fh).get("plugins", {}))
            env["installed_plugins_source"] = str(manifest)
        except Exception:
            pass
    return tuple(sorted(env.items(), key=lambda kv: kv[0]))


def capture_environment(arm: str) -> dict:
    """Record what the run will actually see, so a contaminated arm is detectable.

    Depends only on `arm`, so it is computed once per arm rather than once per
    workspace — a 60-run scaffold was otherwise spawning 58 redundant
    `git rev-parse` subprocesses.
    """
    return dict(_environment(arm))


def workspace_for(root, eval_id, arm, trial):
    return root / f"eval-{eval_id}" / arm / f"trial-{trial}"


def _is_inside(candidate: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        candidate.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def scaffold(evals_path, trials, arms, harness, iteration, workspace_root,
             only_evals, copy_dataset):
    spec = load_evals(evals_path)
    dataset_path = REPO_ROOT / spec["dataset"]["path"]
    if not dataset_path.exists():
        sys.exit(f"dataset not found: {dataset_path}")

    dataset_name = evals_path.parent.name
    if workspace_root is None:
        workspace_root = pathlib.Path(tempfile.gettempdir()) / "last-ds-mile-evals"
    root = pathlib.Path(workspace_root).resolve() / dataset_name / f"iteration-{iteration}"

    if _is_inside(root, REPO_ROOT):
        sys.exit(
            f"REFUSING to scaffold inside the repository ({root}).\n\n"
            "Both arms would inherit this repo's CLAUDE.md, which states the "
            "hard-gate doctrine the without_skill arm is supposed to lack. That is "
            "the iteration-2 contamination path.\n\n"
            "Pass --workspace-root somewhere outside the repo, or omit it to use "
            "the system temp directory."
        )

    selected = [e for e in spec["evals"] if not only_evals or e["id"] in only_evals]
    if not selected:
        sys.exit(f"no evals matched {sorted(only_evals)}")

    made = []
    for ev in selected:
        for arm in arms:
            for trial in range(1, trials + 1):
                ws = workspace_for(root, ev["id"], arm, trial)
                (ws / "outputs").mkdir(parents=True, exist_ok=True)
                (ws / "prompt.md").write_text(ev["prompt"] + "\n", encoding="utf-8")

                if copy_dataset:
                    target = ws / "outputs" / dataset_path.name
                    if not target.exists():
                        shutil.copy2(dataset_path, target)
                    resolved_dataset = target
                else:
                    resolved_dataset = dataset_path

                meta = {
                    "eval_id": ev["id"],
                    "arm": arm,
                    "trial": trial,
                    "prompt": ev["prompt"],
                    "dataset_path": str(resolved_dataset),
                    "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "harness": harness,
                    "iteration": iteration,
                    "workspace_root": str(root),
                    "max_turns": ev.get("max_turns"),
                    "max_cost_usd": ev.get("max_cost_usd"),
                    "environment": capture_environment(arm),
                }
                (ws / "eval_metadata.json").write_text(
                    json.dumps(meta, indent=2), encoding="utf-8"
                )
                made.append((ev["id"], arm, trial, ws))

    _print_instructions(made, root, spec, arms, selected, trials)
    return root


def _print_instructions(made, root, spec, arms, selected, trials):
    print(f"Scaffolded {len(made)} workspaces under\n  {root}\n")
    print(f"  {len(selected)} eval(s) x {len(arms)} arm(s) x {trials} trial(s)\n")
    print("Workspaces are OUTSIDE the repository on purpose — neither arm should")
    print("inherit this repo's CLAUDE.md.\n")
    print(f"  with_skill arm : {spec['arms']['with_skill']}")
    print(f"  without_skill  : {spec['arms']['without_skill']}\n")
    print("Run them with the executor — it builds the per-arm command, so the two")
    print("arms differ by exactly one thing (whether the plugin is loaded), and each")
    print("run records how its own arm was configured:\n")
    print("  python benchmarks/evals/scripts/execute_runs.py \\")
    print(f"      --results-root {root} --dry-run\n")
    print("Do not hand-roll the `claude -p` invocation. Omitting --plugin-dir gives a")
    print("with_skill arm with no plugin loaded — two identical arms, and the exact")
    print("confound that made iteration-2 uninterpretable.\n")
    print("Then grade blind (scripts/grade_manifest.py builds the shuffled, arm-stripped")
    print("manifest), write grading.json next to each transcript, and aggregate:\n")
    print("  python benchmarks/evals/scripts/aggregate.py <dataset> --iteration N \\")
    print(f"      --results-root {root}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("evals_json", help="path to an evals.json (relative to benchmarks/evals/ ok)")
    ap.add_argument("--trials", type=int, default=5, help="trials per case per arm (default 5)")
    ap.add_argument("--arm", choices=["with_skill", "without_skill"], action="append",
                    help="limit to one arm; repeatable. Default: both.")
    ap.add_argument("--evals", type=int, nargs="+", metavar="ID",
                    help="limit to these eval ids (e.g. --evals 3 4 6)")
    ap.add_argument("--harness", default="claude-code",
                    help="label recorded in metadata (practice #8: eval per target harness)")
    ap.add_argument("--iteration", type=int, default=3)
    ap.add_argument("--workspace-root", default=None,
                    help="where to scaffold. Default: system temp. Must be outside the repo.")
    ap.add_argument("--no-copy-dataset", action="store_true",
                    help="reference the dataset by path instead of copying it into each "
                         "workspace (faster, but a run that mutates the data taints the rest)")
    args = ap.parse_args()

    evals_path = pathlib.Path(args.evals_json)
    if not evals_path.is_absolute() and not evals_path.exists():
        evals_path = EVALS_DIR / args.evals_json
    if not evals_path.exists():
        sys.exit(f"evals.json not found: {args.evals_json}")

    arms = args.arm or ["with_skill", "without_skill"]
    scaffold(evals_path, args.trials, arms, args.harness, args.iteration,
             args.workspace_root, set(args.evals or []), not args.no_copy_dataset)


if __name__ == "__main__":
    main()
