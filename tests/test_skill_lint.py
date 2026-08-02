"""Tier 1 of the eval harness: structural rules every SKILL.md must satisfy.

See SPEC-v1-architecture.md §4.1. These are the free, deterministic checks that
define "well-formed" for this pack. They complement test_plugin_structure.py,
which checks *wiring* (commands point at real skills, manifests agree); this file
checks *shape* (descriptions can be routed to, sections are present, links resolve).

The rules are ported from the reference implementation in
addyosmani/agent-skills (`scripts/lib/skill-lint.js`), adapted to this repo's
conventions.

Known offenders are listed in KNOWN_VIOLATIONS below and reported as xfail so CI
stays green while Phase 3 works through them. Deleting an entry from that dict is
how a Phase 3 task gets marked done — the test then enforces the rule for real.
"""

import re
from pathlib import Path

import pytest
from helpers import ROOT, parse_frontmatter

SKILLS_DIR = ROOT / "skills"

# ─── Policy ──────────────────────────────────────────────────────────────────

MAX_DESCRIPTION_CHARS = 1024

KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# A description must say WHEN to use the skill, not only what it does. Accept the
# canonical "Use when ..." plus the "Use before/after/during ..." phrasings already
# in use here. Negated forms describe exclusions, not triggers, so they don't count.
TRIGGER_RE = re.compile(r"\buse (this )?when\b|\buse (before|after|during)\b", re.I)
TRIGGER_NEGATED_RE = re.compile(
    r"\b(do not|don't|never) use (this )?(when|before|after|during)\b", re.I
)

# Each entry is the set of acceptable headings for one required section.
REQUIRED_SECTIONS = [
    ("## Overview",),
    ("## When to Use",),
    ("## Common Rationalizations",),
    ("## Red Flags",),
    ("## Verification",),
]

# Exemptions live HERE, not in skill frontmatter, so a skill cannot excuse itself.
# Every entry needs a written reason.
SECTION_EXEMPT = {
    "ds-method": (
        "Shared discipline layer, not a stage. Its Rationalizations/Red Flags tables "
        "are the ones other skills cite, so it has no separate 'Common Rationalizations' "
        "of its own to restate. Slated to become references/discipline.md in Phase 3."
    ),
}

# Explicit cross-skill reference forms. Generic backticked words are excluded on
# purpose — only these shapes assert "go read that skill".
SKILL_REF_PATTERNS = [
    re.compile(r"\bsee `([a-z][a-z0-9-]+[a-z0-9])`"),
    re.compile(r"\buse the `([a-z][a-z0-9-]+[a-z0-9])` skill"),
    re.compile(r"\bfollow the `([a-z][a-z0-9-]+[a-z0-9])` skill"),
    re.compile(r"\binvoke the `([a-z][a-z0-9-]+[a-z0-9])` skill"),
    re.compile(r"`([a-z][a-z0-9-]+[a-z0-9])` skill\b"),
]

# Rules the current 30-skill layout does not yet satisfy — the Phase 3 worklist
# (tasks/plan-v1-architecture.md §3.5 rewrites every description to the enforced
# formula). Keyed by (skill_name, rule); the value says why it is deferred.
# Deleting an entry is how a Phase 3 task gets marked done.
_ONE_TRIGGER = (
    "Description carries a single trigger clause. Phase 3 §3.5 rewrites it to the "
    "'<verb-s> <object>. Use when A. Use when B.' formula with >=2 distinct "
    "vocabulary slices."
)

KNOWN_VIOLATIONS: dict[tuple[str, str], str] = {
    ("data-science-project", "description-trigger"): (
        "Opens with 'Use at the very start of a tabular ML task', which reads as a "
        "trigger to a human but carries no 'Use when' token for the lexical router. "
        "This is the front door — the one description that most needs to rank first, "
        "and it is the skill that lost routing to /ds in iteration-2 eval-2."
    ),
    ("capturing-learnings", "description-multi-trigger"): _ONE_TRIGGER,
    ("causal-vs-predictive", "description-multi-trigger"): _ONE_TRIGGER,
    ("data-science-project", "description-multi-trigger"): _ONE_TRIGGER,
    ("distribution-shift", "description-multi-trigger"): _ONE_TRIGGER,
    ("ds-data", "description-multi-trigger"): _ONE_TRIGGER,
    ("ds-deploy", "description-multi-trigger"): _ONE_TRIGGER,
    ("ds-evaluate", "description-multi-trigger"): _ONE_TRIGGER,
    ("ds-explain", "description-multi-trigger"): _ONE_TRIGGER,
    ("ds-handoff", "description-multi-trigger"): _ONE_TRIGGER,
    ("ds-model", "description-multi-trigger"): _ONE_TRIGGER,
    ("ds-package", "description-multi-trigger"): _ONE_TRIGGER,
    ("ds-prep", "description-multi-trigger"): _ONE_TRIGGER,
    ("ds-report", "description-multi-trigger"): _ONE_TRIGGER,
    ("uncertainty-quantification", "description-multi-trigger"): _ONE_TRIGGER,
}

FENCE_RE = re.compile(r"^(`{3,})[^\n]*\n.*?^\1[ \t]*$", re.DOTALL | re.MULTILINE)


def strip_fences(text: str) -> str:
    """Drop fenced code blocks so examples and templates don't trip the rules."""
    return FENCE_RE.sub("", text)


def skill_names() -> list[str]:
    return sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())


def skill_path(name: str) -> Path:
    return SKILLS_DIR / name / "SKILL.md"


ALL_SKILLS = skill_names()


def maybe_xfail(name: str, rule: str) -> None:
    reason = KNOWN_VIOLATIONS.get((name, rule))
    if reason:
        pytest.xfail(f"{name} / {rule}: {reason}")


# ─── Frontmatter ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", ALL_SKILLS)
def test_skill_name_is_kebab_and_matches_directory(name):
    frontmatter, _ = parse_frontmatter(skill_path(name))
    assert KEBAB_CASE.match(name), f"{name}: directory must be lowercase-hyphen-separated"
    assert frontmatter.get("name") == name, (
        f"{name}: frontmatter name {frontmatter.get('name')!r} does not match directory"
    )


@pytest.mark.parametrize("name", ALL_SKILLS)
def test_description_length(name):
    maybe_xfail(name, "description-length")
    frontmatter, _ = parse_frontmatter(skill_path(name))
    description = frontmatter.get("description", "")
    assert description, f"{name}: missing description"
    assert len(description) <= MAX_DESCRIPTION_CHARS, (
        f"{name}: description is {len(description)} chars, over the "
        f"{MAX_DESCRIPTION_CHARS} limit"
    )


@pytest.mark.parametrize("name", ALL_SKILLS)
def test_description_states_when_to_use(name):
    """The description is the routing mechanism. Without a trigger clause a skill
    is discoverable only by luck."""
    maybe_xfail(name, "description-trigger")
    frontmatter, _ = parse_frontmatter(skill_path(name))
    description = frontmatter.get("description", "")
    assert TRIGGER_RE.search(description), (
        f"{name}: description has no trigger clause. Add 'Use when ...' "
        f"(or Use before/after/during) so the skill can be routed to."
    )


@pytest.mark.parametrize("name", ALL_SKILLS)
def test_description_trigger_is_not_negated(name):
    """"Do not use when X" is an exclusion, not a trigger. Exclusions belong in
    the body's When to Use section."""
    maybe_xfail(name, "description-trigger-negated")
    frontmatter, _ = parse_frontmatter(skill_path(name))
    description = frontmatter.get("description", "")
    assert not TRIGGER_NEGATED_RE.search(description), (
        f"{name}: description uses a negated trigger form. State exclusions in the "
        f"body under '## When to Use', not in the routing description."
    )


@pytest.mark.parametrize("name", ALL_SKILLS)
def test_description_carries_distinct_trigger_vocabulary(name):
    """Two or more trigger clauses, each carrying different user vocabulary.

    One trigger clause covers one phrasing. Real users say the same thing several
    ways, and the routing index is lexical — see SPEC-v1-architecture.md §2.4.
    """
    maybe_xfail(name, "description-multi-trigger")
    frontmatter, _ = parse_frontmatter(skill_path(name))
    description = frontmatter.get("description", "")
    clauses = TRIGGER_RE.findall(description)
    or_when = len(re.findall(r"\bor when\b", description, re.I))
    assert len(clauses) + or_when >= 2, (
        f"{name}: description has only one trigger clause. Add a second 'Use when ...' "
        f"(or 'or when ...') covering different vocabulary the user might actually say."
    )


# ─── Body structure ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", ALL_SKILLS)
def test_required_sections_present(name):
    if name in SECTION_EXEMPT:
        pytest.skip(f"{name} exempt: {SECTION_EXEMPT[name]}")
    maybe_xfail(name, "required-sections")
    _, body = parse_frontmatter(skill_path(name))
    body = strip_fences(body)
    missing = [
        aliases[0]
        for aliases in REQUIRED_SECTIONS
        if not any(alias in body for alias in aliases)
    ]
    assert not missing, f"{name}: missing required section(s): {', '.join(missing)}"


@pytest.mark.parametrize("name", ALL_SKILLS)
def test_cross_skill_references_resolve(name):
    """Every `see \\`x\\`` / `use the \\`x\\` skill` must name a real skill.

    A dead reference sends the agent looking for a file that isn't there, which
    is how a run ends up doing filesystem archaeology mid-task.
    """
    maybe_xfail(name, "cross-refs")
    _, body = parse_frontmatter(skill_path(name))
    body = strip_fences(body)
    known = set(ALL_SKILLS)
    # Reference-file targets and this repo's own agents are legitimate link
    # destinations that are not skills.
    non_skill_targets = {
        p.stem for p in (ROOT / "references").glob("*.md")
    } | {p.stem for p in (ROOT / "agents").glob("*.md")}

    dead = []
    for pattern in SKILL_REF_PATTERNS:
        for ref in pattern.findall(body):
            if ref not in known and ref not in non_skill_targets:
                dead.append(ref)
    assert not dead, f"{name}: references unknown skill(s): {sorted(set(dead))}"


@pytest.mark.parametrize("name", ALL_SKILLS)
def test_reference_links_resolve_and_are_one_level_deep(name):
    """Relative markdown links from a SKILL.md must exist, and must not chain.

    Deeply nested references cause partial reads: the agent follows the first
    hop, decides it has enough, and never reaches the content that mattered.
    """
    maybe_xfail(name, "ref-depth")
    path = skill_path(name)
    _, body = parse_frontmatter(path)
    body = strip_fences(body)

    links = re.findall(r"\[[^\]]+\]\(([^)#]+\.md)[^)]*\)", body)
    for link in links:
        if link.startswith(("http://", "https://")):
            continue
        target = (path.parent / link).resolve()
        assert target.exists(), f"{name}: dead link to {link}"
        # One level deep: the target must not itself link out to another local .md
        _, target_body = (
            parse_frontmatter(target)
            if target.read_text(encoding="utf-8").startswith("---")
            else ({}, target.read_text(encoding="utf-8"))
        )
        onward = re.findall(r"\[[^\]]+\]\(([^)#]+\.md)[^)]*\)", strip_fences(target_body))
        onward = [
            link_
            for link_ in onward
            if not link_.startswith(("http://", "https://"))
        ]
        assert not onward, (
            f"{name}: {link} links onward to {onward} — keep reference links one "
            f"level deep so the agent reads the whole thing in one hop."
        )


# ─── Catalog-level ───────────────────────────────────────────────────────────


def test_no_orphan_exemptions():
    """Every SECTION_EXEMPT / KNOWN_VIOLATIONS entry must name a skill that exists.

    Stale exemptions silently disable a rule for a skill that was renamed.
    """
    known = set(ALL_SKILLS)
    stale_exempt = sorted(set(SECTION_EXEMPT) - known)
    assert not stale_exempt, f"SECTION_EXEMPT names skills that don't exist: {stale_exempt}"
    stale_known = sorted({n for n, _ in KNOWN_VIOLATIONS} - known)
    assert not stale_known, f"KNOWN_VIOLATIONS names skills that don't exist: {stale_known}"


def test_skill_count_is_intentional():
    """Guardrail against silent catalog growth.

    Every skill costs ~70 tokens of always-on description index and one more
    competitor in the routing space. SPEC-v1-architecture.md §3.3 targets 18;
    this asserts the current number so a new skill is a deliberate edit here.
    """
    assert len(ALL_SKILLS) <= 30, (
        f"{len(ALL_SKILLS)} skills — the catalog grew. Either consolidate, or raise "
        f"this ceiling deliberately and say why in the CHANGELOG."
    )
