# Contributing to Last DS Mile

Thanks for considering a contribution. This is a Claude Code plugin — its "code" is
mostly Markdown (skills, commands, agent prompts) plus a handful of stdlib-only Python
hooks. That keeps the bar for contributing low, but the bar for correctness high: every
skill and command here exists to stop an agent from taking a shortcut a real data
scientist wouldn't take, so changes are held to that standard.

## Repo layout

| Path | What lives there |
|---|---|
| `commands/` | The 17 slash commands (`/ds-frame`, `/ds-model`, …) — thin routers that activate skills |
| `skills/` | The actual discipline: one `SKILL.md` per skill, pipeline-stage skills (`ds-*`) and domain skills (leakage, imbalance, causal-vs-predictive, …) |
| `agents/` | Subagents (`leakage-auditor`, `ds-reviewer`, `data-profiler`) |
| `hooks/` | Four stdlib-only Python hooks (session start, untrusted-input scan, pre-compact, learnings persistence) — see [AUDIT.md](AUDIT.md) |
| `benchmarks/` | Full pipeline runs on real datasets (house-prices, telco-churn, credit-card-fraud) used to validate skill changes end-to-end — see [benchmarks/README.md](benchmarks/README.md); `benchmarks/routing/` holds the trigger corpus and the routing check |
| `tests/` | Plugin-structure and hook-behavior tests (pytest) |
| `lessons/` | Shipped corpus of project-local lessons that auto-resurface |

## The release gate

A change is shippable to `main` when all five hold.

**Free, every PR (CI enforces 1-3):**

1. `pytest` green, including the SKILL.md shape rules in `tests/test_skill_lint.py`.
2. Trigger rank-1 rate at or above the CI floor, no description collision >= 0.75 cosine
   (`benchmarks/routing/route_check.py`).
3. The `data-science-project` vs `cmd:ds` pairwise negative passes. This one is specific
   for a reason: a collision between those two descriptions once sent a modelling request
   to the pipeline *map* instead of the pipeline, so the agent printed a menu and stopped
   instead of answering.

**When skill guidance changes:**

4. If a change would have altered what a committed benchmark run did, re-run the affected
   stage rather than assuming it still holds — and record the re-run in
   [benchmarks/README.md](benchmarks/README.md), including null results. "We checked and
   it held" is worth writing down.

**Always:**

5. Every methodology and results claim in `README.md` and `benchmarks/README.md` is true
   as written. This is not bureaucratic. The plugin's entire proposition is honesty in how
   results are reported; an overclaim in its own documentation is the one bug it cannot
   ship. A `+0.875` gap measured against a hand-written strawman was on the front page
   once. It should not happen twice.

> **On measuring marginal value.** A with/without-skill harness previously lived here. It
> ran once, on two cases and three trials, produced a result that went against the plugin,
> and was then traced to a front-door defect that has since been fixed — so it graded a
> build that no longer existed. It has been removed rather than left to imply a verdict it
> could not support. If you want to reinstate behavioural measurement, the bar to clear is
> real: enough cases and trials to be worth quoting, arms scaffolded outside this
> repository so the "no plugin" arm isn't reading this `CLAUDE.md`, blind grading, and a
> cost budget. Anything less produces a number that looks like evidence and isn't.

## Development setup

Requires Python 3.10–3.13.

```bash
uv pip install pytest pyyaml
python -m pytest
```

There's no package to build and no lockfile — the hooks are pure stdlib by design (see
[AUDIT.md](AUDIT.md) for why: zero network calls, zero dependencies, fully auditable).
`pytest` and `pyyaml` (for parsing `SKILL.md` frontmatter in tests) are the only test
dependencies.

To try the plugin itself against a real Claude Code session, install it locally:

```bash
/plugin marketplace add stamkavid/last-ds-mile
/plugin install last-ds-mile
```

## Making changes

**Editing or adding a skill/command:** keep `SKILL.md`/command frontmatter consistent
with the others in the same directory — tests in `tests/test_plugin_structure.py` check
frontmatter shape and command↔skill wiring. If you add a new pipeline stage command,
wire it into `/ds`'s routing and update the command table in `README.md`.

**Editing a hook:** hooks must stay stdlib-only, make no network calls, and fail open
(never block a tool call — warn, don't stop). Update `AUDIT.md`'s hook table if you
change what a hook reads or writes.

**Validating against real pipelines:** if a change affects skill guidance that a
benchmark exercises, re-run the affected benchmark stage(s) under `benchmarks/` and
confirm the outputs still hold up — these are the regression tests for skill content,
not just code.

## Before opening a PR

- `python -m pytest` passes locally (CI runs it on Python 3.10–3.13).
- Add a `[Unreleased]` entry to [CHANGELOG.md](CHANGELOG.md) describing what changed and
  why (this project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
  [SemVer](https://semver.org/spec/v2.0.0.html)).
- If you touched a hook, re-read [AUDIT.md](AUDIT.md) and keep it accurate — it's the
  trust boundary users rely on before installing.
- Keep PRs scoped to one skill/command/hook where possible; it makes review and
  benchmark re-validation tractable.

## Reporting bugs / proposing skills

Open a GitHub issue. For a new domain skill, briefly describe the failure mode it
catches and, ideally, a real (even anonymized) example of an agent getting it wrong
without the skill — that's the bar the existing skills were written against.

## Security issues

Do not open a public issue for a security concern — see [SECURITY.md](SECURITY.md).
