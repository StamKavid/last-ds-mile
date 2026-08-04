"""Tier 1 of the eval harness: structural rules every SKILL.md must satisfy.

These are the free, deterministic checks that
define "well-formed" for this pack. They complement test_plugin_structure.py,
which checks *wiring* (commands point at real skills, manifests agree); this file
checks *shape* (descriptions can be routed to, sections are present, links resolve).

The rules are ported from the reference implementation in
addyosmani/agent-skills (`scripts/lib/skill-lint.js`), adapted to this repo's
conventions.

Every rule here is enforced for real, with no per-skill escape hatch. If a rule
needs an exception, add it to SECTION_EXEMPT with a written reason — and expect
test_no_orphan_exemptions to fail once that reason stops being true.
"""

import re
from pathlib import Path

import pytest
from helpers import ROOT, parse_frontmatter

SKILLS_DIR = ROOT / "skills"

# ─── Policy ──────────────────────────────────────────────────────────────────

MAX_DESCRIPTION_CHARS = 1024

# Total chars across every skill description — the text that is resident in
# context at all times. Raise deliberately, never to make a failure go away.
ALWAYS_ON_DESCRIPTION_BUDGET = 16000

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
SECTION_EXEMPT: dict[str, str] = {}
"""Skills exempted from the required-section check, each with a written reason.

Empty, and it should stay that way. `ds-method` sat here on the claim that it had
no Rationalizations table of its own; it has had all five sections for some time,
so the exemption was silently skipping the most-cited skill in the pack while the
suite reported green. An exemption that outlives its reason is worse than no rule.
"""

# Explicit cross-skill reference forms. Generic backticked words are excluded on
# purpose — only these shapes assert "go read that skill".
SKILL_REF_PATTERNS = [
    re.compile(r"\bsee `([a-z][a-z0-9-]+[a-z0-9])`"),
    re.compile(r"\buse the `([a-z][a-z0-9-]+[a-z0-9])` skill"),
    re.compile(r"\bfollow the `([a-z][a-z0-9-]+[a-z0-9])` skill"),
    re.compile(r"\binvoke the `([a-z][a-z0-9-]+[a-z0-9])` skill"),
    re.compile(r"`([a-z][a-z0-9-]+[a-z0-9])` skill\b"),
]


FENCE_RE = re.compile(r"^(`{3,})[^\n]*\n.*?^\1[ \t]*$", re.DOTALL | re.MULTILINE)


def strip_fences(text: str) -> str:
    """Drop fenced code blocks so examples and templates don't trip the rules."""
    return FENCE_RE.sub("", text)


def skill_names() -> list[str]:
    return sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())


def skill_path(name: str) -> Path:
    return SKILLS_DIR / name / "SKILL.md"


ALL_SKILLS = skill_names()


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
    ways, and the routing index is lexical.
    """
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
    """Every SECTION_EXEMPT entry must name a skill that exists.

    A stale exemption silently disables a rule for a skill that was renamed — or,
    as happened with `ds-method`, for one that has since started satisfying it.
    """
    known = set(ALL_SKILLS)
    stale_exempt = sorted(set(SECTION_EXEMPT) - known)
    assert not stale_exempt, f"SECTION_EXEMPT names skills that don't exist: {stale_exempt}"



def test_always_on_description_budget():
    """Guard the resource that actually costs something.

    Every skill's description sits in context at all times, whether or not the
    skill is used. Skill *count* is only a proxy for that, and a poor one — with a
    1024-char cap per description, 29 terse skills and 29 maximal ones differ by
    5x in real cost. Budget the characters instead, and name the offenders.
    """
    sizes = {}
    for name in ALL_SKILLS:
        frontmatter, _ = parse_frontmatter(skill_path(name))
        sizes[name] = len(frontmatter.get("description", ""))
    total = sum(sizes.values())
    worst = sorted(sizes.items(), key=lambda kv: -kv[1])[:3]
    assert total <= ALWAYS_ON_DESCRIPTION_BUDGET, (
        f"always-on description index is {total} chars, over the "
        f"{ALWAYS_ON_DESCRIPTION_BUDGET} budget. Largest: "
        + ", ".join(f"{n} ({c})" for n, c in worst)
        + ". Trim one, or raise the budget deliberately and say why in the CHANGELOG."
    )
