"""Guards on how this plugin reaches a user, and on what runs before it does.

Two defects motivated these, both found while checking whether the v1 work was
shippable:

1. `marketplace.json` named the repo with no `ref`, so an install resolved to the
   default branch. `main` had already drifted 4 commits past the `v0.9.0` tag it
   claimed to be, and merging `dev` would have handed everyone 15 commits of
   different content under an identical version string. A version number that
   cannot tell you what you have is not a version number.

2. CI ran on pushes to `master` — 108 commits behind `main`, zero unique commits,
   abandoned — and not on `dev`, the branch every PR actually lands on. Merges to
   the integration branch ran nothing at all.
"""

import json
import re

import yaml
from helpers import ROOT

MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
CI = ROOT / ".github" / "workflows" / "ci.yml"

SEMVER_TAG = re.compile(r"^v\d+\.\d+\.\d+$")


def _load_ci():
    with CI.open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)
    # PyYAML reads a bare `on:` key as the boolean True under YAML 1.1. GitHub
    # parses it as the string "on"; accept whichever the loader produced.
    return workflow, workflow.get("on", workflow.get(True))


def test_marketplace_pins_a_ref():
    """An unpinned source installs whatever is on the default branch right now."""
    with MARKETPLACE.open(encoding="utf-8") as fh:
        marketplace = json.load(fh)
    for plugin in marketplace["plugins"]:
        source = plugin["source"]
        if source.get("source") != "github":
            continue
        pin = source.get("ref") or source.get("sha")
        assert pin, (
            f"{plugin['name']}: github source has no `ref` or `sha`. Installs would "
            f"resolve to the default branch, so what a user gets depends on when they "
            f"install rather than on the version they asked for."
        )
        if source.get("ref"):
            assert SEMVER_TAG.match(source["ref"]), (
                f"{plugin['name']}: ref {source['ref']!r} is not a release tag "
                f"(vX.Y.Z). Pinning to a moving branch is the same defect."
            )


def test_pinned_ref_matches_the_declared_version():
    """The tag users install and the version the plugin reports must agree."""
    with MARKETPLACE.open(encoding="utf-8") as fh:
        marketplace = json.load(fh)
    with PLUGIN.open(encoding="utf-8") as fh:
        version = json.load(fh)["version"]

    for plugin in marketplace["plugins"]:
        ref = plugin["source"].get("ref")
        if not ref:
            continue
        assert ref == f"v{version}", (
            f"marketplace ref {ref!r} does not match plugin.json version {version!r}. "
            f"Bump both together, or a user installing {ref} gets a build that calls "
            f"itself something else."
        )


def test_ci_runs_on_the_integration_branch():
    _, triggers = _load_ci()
    branches = triggers["push"]["branches"]
    assert "dev" in branches, (
        "CI does not run on pushes to `dev`. Every PR lands there first, so without "
        "it the integration branch accumulates unverified work."
    )
    assert "main" in branches, "CI must run on the default branch"


def test_ci_does_not_watch_the_abandoned_branch():
    _, triggers = _load_ci()
    assert "master" not in triggers["push"]["branches"], (
        "`master` is 108 commits behind `main` with no unique commits. Watching it "
        "implies it is live and invites PRs into a dead branch."
    )


def test_ci_can_be_triggered_manually():
    """Without workflow_dispatch there is no way to confirm CI still fires short of
    pushing a commit — which is exactly the position PR #12 left us in."""
    _, triggers = _load_ci()
    assert "workflow_dispatch" in triggers, (
        "ci.yml has no `workflow_dispatch:` trigger, so the workflow cannot be run "
        "by hand to verify it works."
    )


def test_ci_still_runs_on_pull_requests():
    _, triggers = _load_ci()
    assert "pull_request" in triggers, "CI must run on pull requests"
