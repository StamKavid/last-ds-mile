# Last DS Mile

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-8dbb3c)](https://claude.com/claude-code)

A guided data-science lifecycle for [Claude Code](https://claude.com/claude-code) —
with leakage and honesty checks built into every stage.

A product of [The Last AI Mile](https://thelastaimile.substack.com).

```
 FRAME → DATA → EXPLORE → PREP → BASELINE → VALIDATE → MODEL → EVALUATE → EXPLAIN → REPORT → HANDOFF
   0      1        2        3        4          5         6         7         8        9        10
   └──────────────── leakage & honesty gates enforced the whole way down ────────────────┘
```

Data science projects don't die in the modeling cell. They die in the last mile:
target leakage, inflated metrics, a validation scheme that lied, results nobody
trusts, and notebooks nobody can rerun. This plugin walks you through the full
lifecycle on a guided rail, and enforces the discipline that keeps the results honest.

## Quickstart (60-second setup)

**Option A — one command, from any terminal (recommended):**

```bash
npx stamkavid/last-ds-mile
```

This finds your `claude` CLI, adds the marketplace, and installs the plugin —
no npm publish, no account, nothing to configure first.

**Option B — inside Claude Code:**

```
/plugin marketplace add stamkavid/last-ds-mile
/plugin install last-ds-mile
```

Once it's installed: open Claude Code in any project and run `/ds-frame` to start
the pipeline, or `/ds` at any point to see the map and get routed to the next stage.

**Requirements:** [Claude Code](https://claude.com/claude-code) (either option),
plus [Node.js](https://nodejs.org) 18+ if you use the `npx` one-liner.

<details>
<summary><strong>Troubleshooting the install</strong></summary>

If `claude plugin install` fails with `Permission denied (publickey)` or another
SSH clone error, it's trying to clone over SSH but you likely use HTTPS-based
GitHub auth (no SSH key registered). Fix once, globally:

```bash
git config --global url."https://github.com/".insteadOf git@github.com:
```

then re-run the install command.
</details>

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
Each stage writes its output to `.last-ds-mile/stages/` in your project, so later
stages build on earlier ones and `/ds` can detect your progress.

## Discipline, not just steps

Three stages are **Hard Gates** — they stop to ask rather than silently proceed:

- `/ds-model` requires a baseline (`/ds-baseline`) and a validation strategy
  (`/ds-validate`) to exist first.
- `/ds-report` requires slice/subgroup performance from `/ds-evaluate`, not just
  one aggregate metric.
- `/ds-handoff` requires a pinned environment before packaging a model.

See `skills/ds-method/SKILL.md` for the full set of Red Flags and Rationalizations
every stage shares.

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

## Subagents

| Subagent | Model | Use for |
|---|---|---|
| `leakage-auditor` | Opus | Adversarially hunting target/temporal/validation leakage before `/ds-model` or `/ds-report` |
| `ds-reviewer` | Sonnet | Running the discipline checklist (baseline, validation, metric, slices, reproducibility) before `/ds-report` |
| `data-profiler` | Haiku | Fast structural profiling sweep for `/ds-data` or `/ds-explore` |

## Learnings

Four real DS failure-and-fix write-ups ship in `lessons/`, cited from the skills
that teach the pattern they illustrate — read one alongside the skill it's cited
from for a concrete example, not just the abstract rule. Most are tagged to a
pipeline stage, so they surface automatically at the start of a session heading
into that stage.

Run `/ds-learn` to capture your own project-local lesson (what broke, what fixed
it) — it's appended to `.last-ds-mile/learnings.jsonl` and resurfaces the same way.
See the `capturing-learnings` skill for what's worth capturing. Cross-project
sharing of captured lessons is still on the roadmap.

## Safety

This plugin ships a "safe set" of four hooks that **warn, don't block** — none of
them can stop your work:

- scan for untrusted-input risk (a poisoned CSV, a pickle that executes code on
  load, a shell magic hidden in a notebook),
- inject relevant prior learnings at session start,
- persist session state before a compaction, and
- capture a session note on stop.

A sanitization gate is also built into `/ds-data`, and a documented, opt-in
permission baseline lives in [`settings-baseline.json`](settings-baseline.json)
(this plugin never modifies your settings automatically). See
[`AUDIT.md`](AUDIT.md) for exactly what each hook reads, writes, and calls —
**nothing over the network, ever**, and nothing beyond the Python standard library.

To adopt the recommended permission baseline, merge its `"permissions"` block into
your project's `.claude/settings.json` by hand:

```bash
cat settings-baseline.json
```

## Scope — what this does and doesn't cover

Worth knowing before you install:

- **Tabular supervised learning.** Regression and classification on rows and
  columns, via pandas/scikit-learn. No text, vision, recommenders, or time-series
  *forecasting* — time-ordered data is handled as a splitting and leakage concern,
  not as a forecasting stack.
- **The pipeline ends at handoff.** `/ds-handoff` packages a model and pins an
  environment. Deployment, serving, monitoring, drift detection, and retraining
  triggers are **not** covered yet — despite the name, that part of the last mile
  is on the roadmap, not in the box.

## Development

The hooks are pure-standard-library Python 3 — no dependencies, no build step.
The only test dependencies are `pytest` and `PyYAML` (used to parse `SKILL.md`
frontmatter):

```bash
python -m pip install pytest pyyaml
python -m pytest
```

`tests/test_plugin_structure.py` validates plugin structure (frontmatter, required
sections, command↔skill wiring, lesson citations); `tests/test_hooks.py`
unit-tests the runtime hooks' actual behavior via subprocess. CI runs the same
suite on Python 3.10–3.13.
