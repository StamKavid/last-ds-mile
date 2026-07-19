# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] — first public release

The first public release is a focused, pure-markdown Claude Code plugin: the
guided data-science lifecycle (`/ds-frame` → `/ds-handoff`), eight auto-triggering
domain skills, three subagents, four warn-don't-block safety hooks, and a curated
`lessons/` corpus.

### Added

- **The full lifecycle spine** — 11 stage commands from problem framing through
  reproducible handoff, each writing to `.last-ds-mile/stages/` so later stages
  build on earlier ones and `/ds` can route to the next.
- **Three Hard Gates** — `/ds-model` requires a baseline and validation strategy,
  `/ds-report` requires slice performance, `/ds-handoff` requires a pinned
  environment.
- **Eight domain skills** that auto-trigger by description match: leakage
  detection, validation strategy, imbalanced data, metric selection, error
  analysis, notebook hygiene, dataframe performance, data-viz standards.
- **The safe set** — four stdlib-only hooks (`session_start`,
  `scan_untrusted_input`, `pre_compact`, `stop_persist_learnings`), all
  warn-don't-block, documented end to end in [`AUDIT.md`](AUDIT.md) (no network
  calls, ever), plus an opt-in permission baseline in `settings-baseline.json`.
- **Three subagents** — `leakage-auditor` (Opus), `ds-reviewer` (Sonnet),
  `data-profiler` (Haiku).
- **A learnings system** — a curated `lessons/` corpus (four real DS failure/fix
  write-ups, cited from the skills that teach them) plus project-local capture via
  `/ds-learn`, both resurfaced automatically at the start of the next session when
  tagged to the stage you're heading into.
- **A one-command installer** — `npx stamkavid/last-ds-mile` finds your `claude`
  CLI, adds the marketplace, and installs the plugin.

### Notes

- **The experimental Sealed Bet trust-core is not part of this release.** It was
  developed alongside the plugin (a sealed-holdout mechanism with a lift-over-
  baseline ship gate, plus benchmark runs against real Kaggle datasets) and is
  preserved in full on the `archive/sealed-bet` tag. It is moving to a separate,
  standalone home rather than shipping in the flagship plugin — the honesty
  checks in the lifecycle stand on their own without it.

[Unreleased]: https://github.com/stamkavid/last-ds-mile/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/stamkavid/last-ds-mile/releases/tag/v0.2.0
