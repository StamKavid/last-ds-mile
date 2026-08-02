#!/usr/bin/env python3
"""Build a blind grading manifest, and map graded results back afterwards.

SPEC-v1-architecture.md §4.3.3. `benchmarks/evals/README.md` claims the grader is
"deliberately blind to the arm". In iteration-2 it was not: the arm was in every
workspace path, and the grading notes reference it by name ("matches the
without_skill arm's instinct"). For a plugin whose subject is honest reporting,
an unearned methodology claim is the worst kind of bug to ship.

This closes the gap mechanically rather than by asking the grader to look away.

    build   shuffles every {eval, arm, trial} into opaque run ids, copies each
            transcript and outputs/ under that id with no arm in the path, and
            writes a private key file the grader never sees.
    unblind takes the grader's grading.json files (named by run id) and writes
            them back to their true workspaces using the key.

Usage:
    python grade_manifest.py build   --results-root /tmp/last-ds-mile-evals/...
    python grade_manifest.py unblind --results-root /tmp/last-ds-mile-evals/...

stdlib only.
"""
import argparse
import json
import pathlib
import random
import shutil
import sys
import uuid

KEY_NAME = "_blind_key.json"
BLIND_DIR = "_blind"


def iter_workspaces(root: pathlib.Path):
    for meta_path in sorted(root.glob("eval-*/*/trial-*/eval_metadata.json")):
        yield meta_path.parent


def build(root: pathlib.Path, seed: int) -> int:
    workspaces = list(iter_workspaces(root))
    if not workspaces:
        sys.exit(f"no workspaces under {root}")

    blind_root = root / BLIND_DIR
    if blind_root.exists():
        shutil.rmtree(blind_root)
    blind_root.mkdir(parents=True)

    rng = random.Random(seed)
    rng.shuffle(workspaces)

    key = {}
    for workspace in workspaces:
        with (workspace / "eval_metadata.json").open(encoding="utf-8") as fh:
            meta = json.load(fh)
        run_id = uuid.UUID(int=rng.getrandbits(128), version=4).hex[:12]
        target = blind_root / run_id
        target.mkdir()

        # The grader sees the prompt, the expectations it will be given
        # separately, the transcript, and the artifacts. It does not see the arm,
        # the trial number, or any path that encodes them.
        (target / "prompt.md").write_text(meta["prompt"] + "\n", encoding="utf-8")
        (target / "run.json").write_text(json.dumps({
            "run_id": run_id,
            "eval_id": meta["eval_id"],
            "max_turns": meta.get("max_turns"),
            "max_cost_usd": meta.get("max_cost_usd"),
        }, indent=2), encoding="utf-8")

        transcript = workspace / "transcript.jsonl"
        if transcript.exists():
            shutil.copy2(transcript, target / "transcript.jsonl")

        outputs = workspace / "outputs"
        if outputs.exists():
            shutil.copytree(
                outputs, target / "outputs",
                # The dataset is a 144 MB shared input, not evidence of anything.
                ignore=shutil.ignore_patterns("*.csv", "*.parquet", "*.pkl", "*.joblib"),
            )

        key[run_id] = str(workspace.relative_to(root))

    (root / KEY_NAME).write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(f"Blinded {len(key)} run(s) into {blind_root}")
    print(f"Key written to {root / KEY_NAME} — do NOT show this to the grader.\n")
    print("Grade each directory under _blind/ against agents/grader.md, using the")
    print("expectations for its run.json eval_id, and write grading.json inside it.")
    print("Then run: grade_manifest.py unblind --results-root <root>")
    return 0


def unblind(root: pathlib.Path) -> int:
    key_path = root / KEY_NAME
    if not key_path.exists():
        sys.exit(f"no key at {key_path} — run `build` first")
    with key_path.open(encoding="utf-8") as fh:
        key = json.load(fh)

    moved = missing = 0
    for run_id, rel in key.items():
        grading = root / BLIND_DIR / run_id / "grading.json"
        if not grading.exists():
            missing += 1
            continue
        with grading.open(encoding="utf-8") as fh:
            payload = json.load(fh)
        workspace = root / rel
        with (workspace / "eval_metadata.json").open(encoding="utf-8") as fh:
            meta = json.load(fh)
        # Stamp identity back on only after grading, never before.
        payload["eval_id"] = meta["eval_id"]
        payload["_blind_run_id"] = run_id
        payload["_graded_blind"] = True
        (workspace / "grading.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8")
        moved += 1

    print(f"Wrote {moved} grading.json file(s) back to their workspaces.")
    if missing:
        print(f"{missing} blinded run(s) have no grading.json yet.")
    return 1 if missing else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["build", "unblind"])
    ap.add_argument("--results-root", required=True,
                    help="the iteration-N directory run_eval.py scaffolded")
    ap.add_argument("--seed", type=int, default=0, help="shuffle seed (default 0)")
    args = ap.parse_args()

    root = pathlib.Path(args.results_root).resolve()
    if not root.exists():
        sys.exit(f"results root not found: {root}")

    return build(root, args.seed) if args.action == "build" else unblind(root)


if __name__ == "__main__":
    sys.exit(main())
