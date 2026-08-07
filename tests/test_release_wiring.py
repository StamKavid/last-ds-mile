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


def _ci_triggers():
    with CI.open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)
    # PyYAML reads a bare `on:` key as the boolean True under YAML 1.1. GitHub
    # parses it as the string "on"; accept whichever the loader produced.
    return workflow.get("on", workflow.get(True))


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
    triggers = _ci_triggers()
    branches = triggers["push"]["branches"]
    assert "dev" in branches, (
        "CI does not run on pushes to `dev`. Every PR lands there first, so without "
        "it the integration branch accumulates unverified work."
    )
    assert "main" in branches, "CI must run on the default branch"


def test_ci_does_not_watch_the_abandoned_branch():
    triggers = _ci_triggers()
    assert "master" not in triggers["push"]["branches"], (
        "`master` is abandoned. Watching it in CI implies it is live and invites "
        "PRs into a branch nothing ships from. (The archaeology — how far behind "
        "it was when it was retired — belongs in the CHANGELOG, not here, where a "
        "decaying number would undermine the rule at the moment someone reads it.)"
    )


def test_ci_can_be_triggered_manually():
    """Without workflow_dispatch there is no way to confirm CI still fires short of
    pushing a commit — which is exactly the position PR #12 left us in."""
    triggers = _ci_triggers()
    assert "workflow_dispatch" in triggers, (
        "ci.yml has no `workflow_dispatch:` trigger, so the workflow cannot be run "
        "by hand to verify it works."
    )


def test_ci_still_runs_on_pull_requests():
    triggers = _ci_triggers()
    assert "pull_request" in triggers, "CI must run on pull requests"


def test_readme_skill_count_matches_reality():
    """The README claimed 30 skills after the catalog dropped to 29.

    Counts in prose drift silently every time the catalog changes, and a wrong
    count on the front page is the cheapest possible credibility loss.
    """
    actual = len([p for p in (ROOT / "skills").iterdir() if p.is_dir()])
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    claims = {int(n) for n in re.findall(r"(\d+)\s+skills\b", readme)}
    claims |= {int(n) for n in re.findall(r"^## All (\d+) Skills", readme, re.M)}
    wrong = sorted(c for c in claims if c != actual)
    assert not wrong, (
        f"README claims {wrong} skill(s) but there are {actual}. Update the prose "
        f"counts whenever the catalog changes."
    )


def test_readme_lists_every_skill():
    """A skill absent from the README tables is a skill nobody can discover.

    Two were missing (`data-science-project` — the front door — and
    `capturing-learnings`), and the prose breakdown summed to 28 against 29 on
    disk. Counts and tables drift independently; both need checking.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"^\| \[([a-z0-9-]+)\]\(skills/", readme, re.M))
    actual = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}
    assert not (actual - listed), (
        f"skills on disk but absent from the README tables: {sorted(actual - listed)}"
    )
    assert not (listed - actual), (
        f"README tables list skills that no longer exist: {sorted(listed - actual)}"
    )


def test_readme_skill_breakdown_adds_up():
    """The prose breakdown must sum to the real skill count."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    m = re.search(
        r"(\d+) pipeline skills.*?(\d+) domain skills.*?(\d+) shared methodology skill.*?"
        r"(\d+) entry-point skill.*?(\d+) lesson-capture skill",
        readme, re.S,
    )
    assert m, "README no longer states a skill breakdown — update this test or restore it"
    # The breakdown used to sum to 29 only because two errors cancelled: it claimed 12
    # domain skills against 11 on disk, and omitted `capturing-learnings` entirely. Each
    # category is now named, so a miscount can no longer hide behind a correct total.
    total = sum(int(g) for g in m.groups())
    actual = len([p for p in (ROOT / "skills").iterdir() if p.is_dir()])
    assert total == actual, (
        f"README breakdown sums to {total} ({' + '.join(m.groups())}) but there are "
        f"{actual} skills"
    )


def test_readme_does_not_cite_the_removed_illustrative_example():
    """`benchmarks/evals/example/` had a fabricated `without_skill` arm, and its
    +0.875 / +0.80 gaps were being presented on the front page as evidence the
    plugin works. A comparison against a strawman is not evidence."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "evals/example" not in readme, (
        "README references the removed illustrative example tree"
    )
    for fabricated in ("+0.875", "+0.80 "):
        assert fabricated not in readme, (
            f"README still cites {fabricated!r} — a gap measured against an "
            f"illustrative naive baseline, not a live run."
        )
