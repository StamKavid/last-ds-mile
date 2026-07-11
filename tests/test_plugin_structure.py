import json
import re

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
    "capturing-learnings",
]

LESSONS = [
    "the-time-traveling-feature",
    "the-99-percent-fraud-model",
    "the-notebook-nobody-could-rerun",
    "the-leaderboard-that-lied",
]

SKILL_LESSON_CITATIONS = [
    ("target-leakage-detection", "the-time-traveling-feature"),
    ("ds-prep", "the-time-traveling-feature"),
    ("imbalanced-data", "the-99-percent-fraud-model"),
    ("metric-selection", "the-99-percent-fraud-model"),
    ("notebook-hygiene", "the-notebook-nobody-could-rerun"),
    ("ds-handoff", "the-notebook-nobody-could-rerun"),
    ("validation-strategy", "the-leaderboard-that-lied"),
    ("ds-validate", "the-leaderboard-that-lied"),
]

AGENTS = [
    ("leakage-auditor", "opus"),
    ("ds-reviewer", "sonnet"),
    ("data-profiler", "haiku"),
]

REQUIRED_HOOK_EVENTS = ["SessionStart", "PostToolUse", "PreCompact", "Stop"]

HOOK_SCRIPTS = [
    "session_start.py",
    "scan_untrusted_input.py",
    "pre_compact.py",
    "stop_persist_learnings.py",
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


def test_hooks_json_valid():
    path = ROOT / "hooks" / "hooks.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for event in REQUIRED_HOOK_EVENTS:
        assert event in data["hooks"], f"hooks.json missing {event}"


def test_hook_scripts_exist():
    for script in HOOK_SCRIPTS:
        path = ROOT / "hooks" / script
        assert path.exists(), f"missing hooks/{script}"


def test_ds_python_shim_exists():
    path = ROOT / "hooks" / "ds-python.sh"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "python3" in text
    assert "py -3" in text


@pytest.mark.parametrize("agent,model", AGENTS)
def test_agent_structure(agent, model):
    path = ROOT / "agents" / f"{agent}.md"
    assert path.exists(), f"missing agents/{agent}.md"
    frontmatter, body = parse_frontmatter(path)
    assert frontmatter["name"] == agent
    assert frontmatter["model"] == model
    assert "description" in frontmatter
    assert len(body.strip()) > 0


def test_audit_md_documents_every_hook():
    path = ROOT / "AUDIT.md"
    assert path.exists(), "missing AUDIT.md"
    text = path.read_text(encoding="utf-8")
    assert "network" in text.lower()
    for script in HOOK_SCRIPTS:
        assert script in text, f"AUDIT.md doesn't mention {script}"


def test_settings_baseline_valid():
    path = ROOT / "settings-baseline.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    deny = data["permissions"]["deny"]
    for rule in [
        "Read(~/.ssh/**)",
        "Read(~/.aws/**)",
        "Read(**/.env*)",
        "Write(~/.ssh/**)",
        "Write(~/.aws/**)",
        "Bash(curl * | bash)",
        "Bash(curl * | sh)",
    ]:
        assert rule in deny, f"settings-baseline.json missing deny rule {rule}"


def test_ds_data_has_sanitization_gate():
    path = ROOT / "skills" / "ds-data" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    assert "sanitization gate" in text.lower()
    assert "later release of this plugin" not in text


def test_gitignore_covers_last_ds_mile_dir():
    path = ROOT / ".gitignore"
    text = path.read_text(encoding="utf-8")
    assert ".last-ds-mile/" in text


# Mirrors hooks/session_start.py's stdlib-only regex parser (no PyYAML) — do not replace with parse_frontmatter.
@pytest.mark.parametrize("lesson", LESSONS)
def test_lesson_structure(lesson):
    path = ROOT / "lessons" / f"{lesson}.md"
    assert path.exists(), f"missing lessons/{lesson}.md"
    text = path.read_text(encoding="utf-8")
    assert re.search(r"^title:\s*.+$", text, re.MULTILINE), f"{lesson} missing title:"
    assert re.search(r"^skills:\s*\[.+\]\s*$", text, re.MULTILINE), f"{lesson} missing skills: [...]"
    assert re.search(r"^stages:\s*\[.*\]\s*$", text, re.MULTILINE), f"{lesson} missing stages: [...]"


def test_ds_learn_command_exists():
    path = ROOT / "commands" / "ds-learn.md"
    assert path.exists(), "missing commands/ds-learn.md"
    frontmatter, body = parse_frontmatter(path)
    assert "description" in frontmatter
    assert "capturing-learnings" in body


@pytest.mark.parametrize("skill,lesson", SKILL_LESSON_CITATIONS)
def test_skill_cites_lesson(skill, lesson):
    path = ROOT / "skills" / skill / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    assert lesson in text, f"{skill}/SKILL.md doesn't cite lessons/{lesson}.md"


def test_package_json_valid():
    path = ROOT / "package.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["name"] == "last-ds-mile"
    assert data["bin"]["last-ds-mile"] == "bin/install.mjs"
    assert data["private"] is True


def test_install_script_exists():
    path = ROOT / "bin" / "install.mjs"
    assert path.exists(), "missing bin/install.mjs"
    text = path.read_text(encoding="utf-8")
    assert "marketplace add" in text
    assert "plugin install" in text


def test_license_exists():
    path = ROOT / "LICENSE"
    assert path.exists(), "missing LICENSE"
    assert "MIT" in path.read_text(encoding="utf-8")


def test_readme_documents_npx_install():
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    assert "npx stamkavid/last-ds-mile" in text


def test_sealed_bet_core_is_importable_without_plugin_adapter():
    # The portable core must not import any Claude-Code-only module.
    import importlib
    for mod in ["sealed_bet.seal", "sealed_bet.score", "sealed_bet.metrics",
                "sealed_bet.contract", "sealed_bet.ledger", "sealed_bet.splits",
                "sealed_bet.state"]:
        importlib.import_module(mod)


def test_seal_and_open_commands_exist():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    assert (root / "commands" / "ds-seal.md").exists()
    assert (root / "commands" / "ds-open.md").exists()
