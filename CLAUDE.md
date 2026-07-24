# CLAUDE.md

Instructions for Claude Code when working in this repository.

## What this repo is

A Claude Code plugin that packages data-science lifecycle discipline as skills and
slash commands (`commands/` route to `skills/`, one `SKILL.md` per skill). The product
is the Markdown itself — the guidance an agent follows when it runs `/ds-frame`,
`/ds-model`, etc. in *someone else's* project. Precision and honesty in that guidance
matters more than usual: a skill that's vague or wrong doesn't just read badly, it lets
an agent ship a leaky model or an overreached causal claim in a real project.

## Hard rules

- **Hooks (`hooks/*.py`) stay stdlib-only, zero network calls, fail-open (warn, never
  block).** This is a load-bearing trust claim documented in [AUDIT.md](AUDIT.md) —
  if you touch a hook, update that file's table in the same change.
- **Don't invent scope.** Skills here encode discipline someone already got burned by
  not having — see the CHANGELOG entries for the story behind most of them. A new
  skill needs a concrete failure mode it catches, not a hypothetical one.
- **Command ↔ skill wiring must stay consistent** — `tests/test_plugin_structure.py`
  checks frontmatter shape and that commands reference real skills. Run `pytest`
  before treating a commands/skills change as done.
- **The three hard-gate stages stay hard gates**: `/ds-model` requires a baseline and
  validation strategy to already exist; `/ds-report` requires subgroup performance, not
  just an aggregate metric; `/ds-handoff` requires a pinned environment. Don't soften
  these without discussing it explicitly — they're the whole point of the plugin.

## Working in this repo

```bash
uv pip install pytest pyyaml
python -m pytest          # only test deps; no lockfile, no package to build
```

Use `uv pip install`, never `pip install` directly.

- `benchmarks/` holds full `/ds-frame` → `/ds-handoff` pipeline runs on real datasets
  (house-prices, telco-churn, credit-card-fraud). Treat these as regression tests for
  skill *content*: if a skill's guidance changes in a way that would change what an
  earlier benchmark run did, re-run the affected stage(s) rather than assuming it's
  still consistent.
- Add a `[Unreleased]` entry to `CHANGELOG.md` for any user-facing change (new skill,
  new command, behavior change to an existing one). Keep-a-Changelog format, SemVer.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution workflow and
  [SECURITY.md](SECURITY.md) for how to handle anything security-sensitive you find.

## Style

- Skills and commands are Markdown prose, not code — write them the way you'd want a
  sharp but rushed colleague to read them: direct, no filler, concrete examples over
  abstract principles.
- Don't add a skill/command comment or meta-note explaining what a file is for beyond
  its own frontmatter `description` — the description *is* the routing mechanism other
  commands and `/ds` rely on to find it.
