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

## Domain skills

These aren't slash commands — they auto-trigger by description match whenever a
situation calls for them, whether or not you're mid-pipeline:

| Skill | Fires when |
|---|---|
| `target-leakage-detection` | a metric looks too good on the first try, or a feature dominates importance |
| `validation-strategy` | setting up CV, or deciding whether hyperparameter tuning needs nested CV |
| `imbalanced-data` | a classification target is skewed and accuracy stops being trustworthy |
| `metric-selection` | choosing or defending an evaluation metric |
| `error-analysis` | a model's aggregate score looks fine but you need to know where it fails |
| `notebook-hygiene` | finishing exploratory work that will be shared or handed off |
| `dataframe-performance` | a pandas operation is slow, or deciding whether to reach for Polars |
| `data-viz-standards` | building EDA plots, or preparing stakeholder-facing figures and tables |

## Status

This release covers the full lifecycle spine, 8 domain skills (leakage detection,
validation strategy, imbalanced data, metric selection, error analysis, notebook
hygiene, dataframe performance, and data viz standards) that auto-trigger whenever a
matching situation comes up, and the safe set: 4 hooks, a documented permission
baseline, a real sanitization gate in `/ds-data`, `AUDIT.md`, and 3 subagents
(`leakage-auditor`, `ds-reviewer`, `data-profiler`). See the "Safety" section below.
The learnings system now ships too: a curated `lessons/` corpus (4 real DS
failure/fix write-ups, cited from the skills that teach them) and project-local
capture via `/ds-learn`, which resurfaces relevant lessons automatically at the
start of your next session. Cross-project sharing of captured lessons is still
on the roadmap.

## Safety

This plugin ships a "safe set": hooks that scan for untrusted-input risk (a
poisoned CSV, a pickle file that executes code on load, a shell magic hidden in a
notebook), a sanitization gate built into `/ds-data`, and 3 subagents. Every hook
is **warn, don't block** — nothing here silently stops your work. See
[`AUDIT.md`](AUDIT.md) for exactly what each hook reads, writes, and calls (nothing
over the network, ever).

To adopt the recommended permission baseline in your own project, merge
[`settings-baseline.json`](settings-baseline.json) into your project's
`.claude/settings.json` (this plugin never modifies your settings automatically):

    cat settings-baseline.json
    # then merge its "permissions" block into your own settings.json by hand,
    # or with a JSON-merging tool if you already have one in your workflow.

### Subagents

| Subagent | Model | Use for |
|---|---|---|
| `leakage-auditor` | Opus | Adversarially hunting target/temporal/validation leakage before `/ds-model` or `/ds-report` |
| `ds-reviewer` | Sonnet | Running the discipline checklist (baseline, validation, metric, slices, reproducibility) before `/ds-report` |
| `data-profiler` | Haiku | Fast structural profiling sweep for `/ds-data` or `/ds-explore` |

## Learnings

Four real DS failure-and-fix write-ups ship in `lessons/`, cited from the
skills that teach the pattern they illustrate — read one alongside the skill
it's cited from for a concrete example, not just the abstract rule.

Run `/ds-learn` to capture your own project-local lesson (what broke, what
fixed it) — it's appended to `.last-ds-mile/learnings.jsonl` and automatically
resurfaces at the start of your next session if it's tagged to the stage
you're about to work on. See the `capturing-learnings` skill for what's worth
capturing.

## Development

    pip install -r requirements-dev.txt
    python -m pytest tests/ -v

`tests/` validates plugin structure (frontmatter, required sections, command↔skill
wiring) — there's no runtime code to unit test yet.
