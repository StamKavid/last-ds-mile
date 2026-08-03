"""Guards on the eval harness itself.

The harness is how this pack knows whether it works. Iteration-2's numbers turned
out to be unusable not because the skills were wrong but because the harness let
both arms share a CLAUDE.md, recorded nothing about the environment, and graded
with the arm visible in every path. These tests make those specific regressions
impossible to reintroduce quietly.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from helpers import ROOT

SCRIPTS = ROOT / "benchmarks" / "evals" / "scripts"
CASES = ROOT / "benchmarks" / "evals" / "cases"
SKILLS = ROOT / "skills"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


route_check = _load("route_check")


# ─── Routing ─────────────────────────────────────────────────────────────────


def test_every_skill_has_a_trigger_case_file():
    """A skill with no case file is a skill nobody has checked is reachable."""
    skills = {p.name for p in SKILLS.iterdir() if p.is_dir()}
    cases = {p.stem for p in CASES.glob("*.json")}
    missing = sorted(skills - cases)
    assert not missing, (
        f"no benchmarks/evals/cases/<name>.json for: {missing}. Every skill ships "
        f"with at least 3 positive and 2 negative trigger prompts."
    )
    orphan = sorted(cases - skills)
    assert not orphan, f"case files for skills that no longer exist: {orphan}"


@pytest.mark.parametrize("path", sorted(CASES.glob("*.json")), ids=lambda p: p.stem)
def test_case_file_shape(path):
    case = json.loads(path.read_text(encoding="utf-8"))
    assert case["skill_name"] == path.stem
    positive = case["trigger"]["positive"]
    negative = case["trigger"]["negative"]
    assert len(positive) >= 3, f"{path.stem}: needs >=3 positive trigger prompts"
    assert len(negative) >= 2, f"{path.stem}: needs >=2 negative trigger prompts"
    for neg in negative:
        assert neg.get("owner"), (
            f"{path.stem}: negative prompt {neg['prompt']!r} has no `owner`. Without "
            f"one the assertion passes vacuously whenever the prompt matches nothing."
        )


def test_negative_owners_exist():
    known = {p.name for p in SKILLS.iterdir() if p.is_dir()}
    known |= {f"cmd:{p.stem}" for p in (ROOT / "commands").glob("*.md")}
    for path in sorted(CASES.glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        for neg in case["trigger"]["negative"]:
            assert neg["owner"] in known, (
                f"{path.stem}: negative owner {neg['owner']!r} is not a skill or command"
            )


def test_routing_holds_at_the_ci_floor():
    """The regression guard. Mirrors the CI step, so a bad description edit fails
    locally before it reaches a PR."""
    descriptions = route_check.load_descriptions()
    tfs, idf = route_check.build_corpus(descriptions)
    aliases = route_check.build_alias_map()
    cases = route_check.load_cases()
    result = route_check.check_triggers(cases, tfs, idf, descriptions, aliases)

    assert not result["failures"], (
        "routing assertions failed:\n  " + "\n  ".join(result["failures"])
    )
    assert result["rank1_rate"] >= 85.0, (
        f"rank-1 routing fell to {result['rank1_rate']}% (floor 85%). "
        f"Fix the description, not the eval."
    )


def test_no_description_collisions():
    descriptions = route_check.load_descriptions()
    tfs, idf = route_check.build_corpus(descriptions)
    aliases = route_check.build_alias_map()
    collisions = route_check.check_collisions(tfs, idf, aliases)
    assert not collisions["errors"], (
        f"description pairs at or above {route_check.COLLISION_ERROR} cosine — merge "
        f"them or rewrite one: {collisions['errors']}"
    )


# ─── Behavioral harness ──────────────────────────────────────────────────────


def test_run_eval_refuses_to_scaffold_inside_the_repo():
    """The iteration-2 contamination path, closed structurally.

    Both arms under this repo's CLAUDE.md means the `without_skill` arm reads the
    hard-gate doctrine it is supposed to lack.
    """
    run_eval = _load("run_eval")
    assert run_eval._is_inside(ROOT / "benchmarks" / "x", ROOT)
    assert not run_eval._is_inside(Path("/tmp/somewhere"), ROOT)


@pytest.mark.parametrize("dataset", ["credit-card-fraud", "house-prices"])
def test_evals_carry_budgets_and_a_completion_expectation(dataset):
    spec = json.loads(
        (ROOT / "benchmarks" / "evals" / dataset / "evals.json").read_text(encoding="utf-8")
    )
    for ev in spec["evals"]:
        assert ev.get("max_turns"), f"{dataset} eval {ev['id']}: no max_turns budget"
        assert ev.get("max_cost_usd"), f"{dataset} eval {ev['id']}: no max_cost_usd budget"
        if ev.get("category") == "negative-trigger":
            continue
        # A run that stalls without a verdict should fail one named check, not
        # three content checks by accident — that is what obscured iteration-2.
        assert any("does not end by asking" in e for e in ev["expectations"]), (
            f"{dataset} eval {ev['id']}: no completion expectation"
        )


@pytest.mark.parametrize("dataset", ["credit-card-fraud", "house-prices"])
def test_pressure_cases_exist(dataset):
    """Discipline that only holds when nobody argues against it isn't discipline."""
    spec = json.loads(
        (ROOT / "benchmarks" / "evals" / dataset / "evals.json").read_text(encoding="utf-8")
    )
    families = {e.get("category", "") for e in spec["evals"]}
    assert any(f.startswith("pressure-") for f in families), (
        f"{dataset}: no pressure case. Add at least one of authority / time / "
        f"sunk-cost pressure, per SPEC-v1-architecture.md §4.4."
    )


def test_eval_results_are_not_committed_by_default():
    ignore = (ROOT / "benchmarks" / "evals" / ".gitignore").read_text(encoding="utf-8")
    assert "results/" in ignore, (
        "benchmarks/evals/.gitignore must exclude generated run workspaces — they "
        "carry multi-hundred-MB dataset copies."
    )


def test_executor_separates_the_arms_by_plugin_loading():
    """The arms must differ by exactly one thing: whether the plugin is loaded.

    Iteration-2 recorded no arm toggle at all, so a surprising result could not be
    separated from a misconfigured run.
    """
    execute_runs = _load("execute_runs")
    prompt = "does this model work"
    with_skill = execute_runs.build_command(
        Path("/tmp/ws"), {"arm": "with_skill", "prompt": prompt}, "claude")
    without = execute_runs.build_command(
        Path("/tmp/ws"), {"arm": "without_skill", "prompt": prompt}, "claude")

    assert "--plugin-dir" in with_skill, "with_skill arm must load the plugin"
    assert "--plugin-dir" not in without, "without_skill arm must not load the plugin"
    assert [c for c in with_skill if c != "--plugin-dir"
            and not c.endswith("last-ds-mile")] == without, (
        "the arms differ by more than plugin loading — any other difference "
        "confounds the comparison"
    )


def test_executor_requires_confirmation_before_spending():
    """A script that spends money on import or on a bare invocation is a trap."""
    source = (SCRIPTS / "execute_runs.py").read_text(encoding="utf-8")
    assert "--dry-run" in source, "executor must offer a dry run"
    assert 'input(' in source, "executor must confirm before spending"
    assert "--yes" in source, "unattended runs must be opt-in and explicit"
