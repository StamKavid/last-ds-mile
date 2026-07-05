import json

import pytest

from helpers import ROOT, parse_frontmatter

STAGE_SKILLS = [
    "ds-frame",
    "ds-data",
    "ds-explore",
    "ds-prep",
    "ds-baseline",
    "ds-validate",
    "ds-model",
    "ds-evaluate",
    "ds-explain",
    "ds-report",
    "ds-handoff",
]

DOMAIN_SKILLS = [
    "target-leakage-detection",
    "validation-strategy",
    "imbalanced-data",
    "metric-selection",
    "error-analysis",
    "notebook-hygiene",
    "dataframe-performance",
    "data-viz-standards",
]

REQUIRED_SECTIONS = [
    "## Overview",
    "## When to Use",
    "## Core Process",
    "## Common Rationalizations",
    "## Red Flags",
    "## Verification",
]


def test_plugin_json_valid():
    path = ROOT / ".claude-plugin" / "plugin.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["name"] == "last-ds-mile"
    assert "description" in data
    assert "version" in data


def test_marketplace_json_valid():
    path = ROOT / ".claude-plugin" / "marketplace.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["name"] == "last-ds-mile"
    assert len(data["plugins"]) == 1
    assert data["plugins"][0]["name"] == "last-ds-mile"
    assert data["plugins"][0]["source"]["repo"] == "stamkavid/last-ds-mile"


def test_ds_method_skill_structure():
    path = ROOT / "skills" / "ds-method" / "SKILL.md"
    frontmatter, body = parse_frontmatter(path)
    assert frontmatter["name"] == "ds-method"
    assert len(frontmatter["description"]) <= 1024
    assert "## Red Flags" in body
    assert "## Common Rationalizations" in body
    assert "## Hard Gates" in body


@pytest.mark.parametrize("stage", STAGE_SKILLS)
def test_stage_skill_structure(stage):
    path = ROOT / "skills" / stage / "SKILL.md"
    assert path.exists(), f"missing skills/{stage}/SKILL.md"
    frontmatter, body = parse_frontmatter(path)
    assert frontmatter["name"] == stage
    assert len(frontmatter["description"]) <= 1024
    for section in REQUIRED_SECTIONS:
        assert section in body, f"{stage} missing section {section}"


@pytest.mark.parametrize("stage", STAGE_SKILLS)
def test_stage_command_exists(stage):
    path = ROOT / "commands" / f"{stage}.md"
    assert path.exists(), f"missing commands/{stage}.md"
    frontmatter, body = parse_frontmatter(path)
    assert "description" in frontmatter
    assert stage in body, f"commands/{stage}.md doesn't reference the {stage} skill"


def test_ds_router_command_lists_all_stages():
    path = ROOT / "commands" / "ds.md"
    text = path.read_text(encoding="utf-8")
    for stage in STAGE_SKILLS:
        assert f"/{stage}" in text, f"router doesn't mention /{stage}"


@pytest.mark.parametrize("skill", DOMAIN_SKILLS)
def test_domain_skill_structure(skill):
    path = ROOT / "skills" / skill / "SKILL.md"
    assert path.exists(), f"missing skills/{skill}/SKILL.md"
    frontmatter, body = parse_frontmatter(path)
    assert frontmatter["name"] == skill
    assert len(frontmatter["description"]) <= 1024
    for section in REQUIRED_SECTIONS:
        assert section in body, f"{skill} missing section {section}"
