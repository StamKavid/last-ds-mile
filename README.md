# Last DS Mile

A guided data-science lifecycle for [Claude Code](https://claude.com/claude-code) —
frame, explore, baseline, validate, model, evaluate, and report — with leakage and
honesty checks built into every stage.

A product of [The Last AI Mile](https://thelastaimile.substack.com).

## Why

Data science projects don't die in the modeling cell. They die in the last mile: target
leakage, inflated metrics, a validation scheme that lied, results nobody trusts, and
notebooks nobody can rerun. This plugin walks you through the full lifecycle on a guided
rail, and enforces the discipline that keeps the results honest.

## Install

    /plugin marketplace add stamkavid/last-ds-mile
    /plugin install last-ds-mile

## The pipeline

| # | Command | Stage |
|---|---------|-------|
| 0 | `/ds-frame` | Problem framing |
| 1 | `/ds-data` | Data understanding |
| 2 | `/ds-explore` | EDA |
| 3 | `/ds-prep` | Cleaning + feature engineering |
| 4 | `/ds-baseline` | Honest baseline |
| 5 | `/ds-validate` | Validation design |
| 6 | `/ds-model` | Modeling |
| 7 | `/ds-evaluate` | Evaluation + error analysis |
| 8 | `/ds-explain` | Interpretation |
| 9 | `/ds-report` | Communication |
| 10 | `/ds-handoff` | Reproducibility & handoff |

Run `/ds` at any point to see the pipeline map and get routed to the next stage.

Each stage writes its output to `.last-ds-mile/stages/` in your project, so later stages
build on earlier ones and `/ds` can detect your progress.

## Discipline, not just steps

Three stages are Hard Gates and will stop to ask rather than silently proceed:
- `/ds-model` requires a baseline (`/ds-baseline`) and a validation strategy
  (`/ds-validate`) to exist first.
- `/ds-report` requires slice/subgroup performance from `/ds-evaluate`, not just one
  aggregate metric.
- `/ds-handoff` requires a pinned environment before packaging a model.

See `skills/ds-method/SKILL.md` for the full set of Red Flags and Rationalizations every
stage shares.

## Status

This is an early release covering the full lifecycle spine. Domain-specific skills
(leakage detection, imbalanced data, time-series CV, etc.), the safe-set of hooks and
permission guidance, and the cross-project learnings system are on the roadmap — see
the design spec linked from the project history for the full plan.

## Development

    pip install -r requirements-dev.txt
    python -m pytest tests/ -v

`tests/` validates plugin structure (frontmatter, required sections, command↔skill
wiring) — there's no runtime code to unit test yet.
