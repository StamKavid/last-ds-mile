# Last DS Mile

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-8dbb3c)](https://claude.com/claude-code)

A guided data-science lifecycle for [Claude Code](https://claude.com/claude-code) —
frame, explore, baseline, validate, model, evaluate, and report — with leakage and
honesty checks built into every stage.

A product of [The Last AI Mile](https://thelastaimile.substack.com).

## Scope — what this does and doesn't cover

Worth knowing before you install, so nothing here is a surprise later:

- **Tabular supervised learning.** Regression and classification on rows and
  columns, via pandas/scikit-learn (and AutoGluon for the optional Build loop).
  No text, vision, recommenders, or time-series *forecasting* — time-ordered
  data is handled as a splitting and leakage concern, not as a forecasting stack.
- **The pipeline ends at handoff.** `/ds-handoff` packages a model and pins an
  environment. Deployment, serving, monitoring, drift detection, and retraining
  triggers are **not** covered yet — despite the name, that part of the last mile
  is on the roadmap, not in the box.
- **The Sealed Bet is experimental, and its guard is friction rather than a
  sandbox.** `seal_guard.py` denies the `Read` tool on sealed label files;
  `Bash` and `Grep` are **not** gated, so an agent that runs `cat` or `grep` can
  still reach them. Treat it as a mechanism that makes peeking deliberate and
  visible, not as one that makes it impossible. See [`AUDIT.md`](AUDIT.md).

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

Either way, once it's installed: open Claude Code in any project and run
`/ds-frame` to start the pipeline, or `/ds` at any point to see the map and get
routed to the next stage.

**Requirements:** [Claude Code](https://claude.com/claude-code) (either option),
plus [Node.js](https://nodejs.org) 18+ if you use the `npx` one-liner.

**Troubleshooting:** if `claude plugin install` fails with `Permission denied
(publickey)` or another SSH clone error, it's trying to clone over SSH but you
likely use HTTPS-based GitHub auth (no SSH key registered). Fix once, globally:

```bash
git config --global url."https://github.com/".insteadOf git@github.com:
```

then re-run the install command.

## Why

Data science projects don't die in the modeling cell. They die in the last mile: target
leakage, inflated metrics, a validation scheme that lied, results nobody trusts, and
notebooks nobody can rerun. This plugin walks you through the full lifecycle on a guided
rail, and enforces the discipline that keeps the results honest.

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

## The Sealed Bet (experimental)

A trust core you can run in any coding agent: `python -m sealed_bet.seal` locks a
holdout's labels and records a Contract — against a real non-ML heuristic baseline if
you pass one (`--baseline-py path/to/file.py:function`; otherwise a constant
median/mean, which for `roc_auc` scores exactly 0.5 on every dataset by construction and
isn't much of a rival). Supports `rmse`, `roc_auc`, and `auprc` (a materially better fit
than `roc_auc` for an imbalanced classification decision, since its constant baseline
converges to the positive-class prevalence rather than a universal 0.5). A `random`
split on a classification target stratifies by the target automatically — no flag
needed — and `--exclude-from-features col1,col2` keeps a column (e.g. a raw `time_col`
with no standalone predictive legitimacy) out of the model's own inputs while still
using it to build the split. You build freely on the dev split; then `python -m
sealed_bet.score` opens the holdout **once** and reports `lift = (sealed − baseline)/σ`,
where predictions are joined to the sealed labels on a `row_id` echoed from
`held/row_ids.csv` rather than by row position — so a pipeline that sorts or reindexes
before writing `preds.csv` gets a hard error instead of a silently wrong verdict, and
where σ is the paired bootstrap difference between the model's and baseline's scores on
the same held rows — ship only if it beats the baseline by more than the noise (> 2σ).
Opening also writes `held/revealed.csv` (the true target plus your submitted
predictions) so `/ds-evaluate`/`/ds-explain` can legitimately compute slice/calibration/
importance numbers afterward, without a second look at the sealed labels. `seal()` also
runs two non-blocking Probes and records both verdicts in the Ledger — the
split-adversary (certifies dev/held are statistically indistinguishable, the right check
for a `random`/`group` split) and the leakage-adversary (flags any single feature whose
solo predictive power is implausibly high) — both warn-only, so a failed probe never
stops the seal. The scoring/contract/ledger math itself has zero Claude-Code-only
imports, so it's portable to any agent. The physical Read-blocking (`seal_guard` hook)
is a Claude Code-specific hook this plugin ships, and it currently gates the `Read` tool
only — `Bash`/`Grep` are not gated, so a careless or malicious agent could still
`cat`/`grep` the sealed file directly and bypass the guard. In Claude Code, use
`/ds-seal` and
`/ds-open`.

**Real runs, not just design:** `benchmarks/` holds three full pipeline runs against real
Kaggle datasets, kept as durable evidence (stage docs, Contract, Ledger — not the raw
data or model binaries). See [`BENCHMARKS.md`](BENCHMARKS.md) for what running the plugin
against real data found and fixed that reading the code alone didn't.

## Results

| Dataset | Task | Metric | Real heuristic baseline | Sealed score | Lift | Honest ceiling |
|---|---|---|---|---|---|---|
| [House Prices](benchmarks/house-prices/) (Ames) | regression | RMSE, log ↓ | 0.2487 — neighborhood median price per sqft | **0.1311** | 9.46σ | ~0.115 |
| [Telco Churn](benchmarks/telco-churn/) (IBM) | classification | ROC-AUC ↑ | 0.7420 — churn rate per contract type | **0.8471** | 11.68σ | ~0.85 |
| [Credit Card Fraud](benchmarks/credit-card-fraud/) (ULB) | classification | AUPRC ↑ | 0.0518 — unsupervised anomaly distance | **0.8158** | 20.45σ | ~0.85 |

**How to read this table.** These are single honest runs, not leaderboard entries. Each
score is measured **once**, on a holdout sealed before modeling began, against a real
non-ML heuristic rather than a constant — for AUPRC on the fraud set, a constant scores
the positive-class prevalence, ~0.0017, so the 0.0518 anomaly rule is roughly 30× a
floor rather than a rival. The "honest ceiling" is a human, community-informed estimate
of what each problem tops out at *without* overfitting to a years-public test set; we
compare against that on purpose rather than the public leaderboard, which in all three
communities is understood to contain leaked and overfit submissions. Exact numbers shift
between re-seals (AutoGluon's internal search is unseeded) — the mechanism and its
reproducibility are the claim, not the decimals.

**What the benchmarks found is the more useful output.** Running these surfaced ~15 real
product defects that reading the code did not, all recorded in
[`BENCHMARKS.md`](BENCHMARKS.md): a ship gate computing the wrong σ, two adversary probes
that had never once run on a realistic dataset, a baseline that was never a real rival,
predictions joined to labels by row position, and a warn-only probe costing 10× the model
it protects. The fraud benchmark also ran under *both* split strategies to test whether a
random split inflates scores on time-ordered data. **It didn't** — the predicted result
failed to reproduce, and [that report](benchmarks/credit-card-fraud/REPORT.md) says so
plainly instead of reframing it.

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
matching situation comes up, and the safe set: 5 hooks, a documented permission
baseline, a real sanitization gate in `/ds-data`, `AUDIT.md`, and 3 subagents
(`leakage-auditor`, `ds-reviewer`, `data-profiler`). See the "Safety" section below.
The learnings system now ships too: a curated `lessons/` corpus (4 real DS
failure/fix write-ups, cited from the skills that teach them) and project-local
capture via `/ds-learn` — both resurface automatically at the start of your
next session if tagged to the stage you're about to work on. Cross-project
sharing of captured lessons is still on the roadmap.

## Safety

This plugin ships a "safe set": hooks that scan for untrusted-input risk (a
poisoned CSV, a pickle file that executes code on load, a shell magic hidden in a
notebook), a sanitization gate built into `/ds-data`, and 3 subagents. 4 of the 5
hooks are **warn, don't block** — they never stop your work. The one exception is
`seal_guard.py`, which deliberately denies Read access to the sealed holdout
labels — that block is the physical basis of the Sealed Bet's trust guarantee
for the `Read` tool specifically; `Bash`/`Grep` are not yet gated (see AUDIT.md's
"Known limitation" note under `seal_guard.py`).
See [`AUDIT.md`](AUDIT.md) for exactly what each hook reads, writes, and calls
(nothing over the network, ever).

### Independent scan

This plugin is scanned with [NVIDIA SkillSpector](https://github.com/NVIDIA/skillspector)
(v2.3.13, static analysis) on every push, and the scan gates CI. Reproduce it:

    uv tool install git+https://github.com/NVIDIA/skillspector.git
    skillspector scan . --no-llm --baseline .skillspector-baseline.yaml

**Read the number honestly:** the result is 0/100 (SAFE) *with 31 findings
suppressed* via [`.skillspector-baseline.yaml`](.skillspector-baseline.yaml).
A suppressed finding is not a finding that vanished — so every entry in that
file carries a written reason, and CI fails on any finding that doesn't have
one. Inspect them yourself with `--show-suppressed`. The two largest groups:

- **5 dependency CVE findings (3 CRITICAL)** against numpy/pandas/scikit-learn/
  PyYAML/pytest. SkillSpector's `SC4` check queries OSV by package *name* and
  reports every advisory ever filed, without filtering by the version declared —
  verified by raising the floors to numpy 2.3 / scikit-learn 1.7 / PyYAML 6.0.2
  and re-scanning, which changed nothing. Any project depending on the standard
  DS stack scores 100/100 "DO NOT INSTALL" here regardless of what it pins.
- **4 "external script fetching" findings (HIGH)** matching the literal string
  `curl * | bash`. In both files it appears, that string is the *deny rule*
  blocking the pattern — in `settings-baseline.json`'s `permissions.deny`, and
  in the test asserting that rule exists.

There is no NVIDIA verification or certification programme, and this is not one:
it's a self-run scan, reproducible with the command above.

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
it's cited from for a concrete example, not just the abstract rule. Most of
them are also tagged to a pipeline stage, so it will surface automatically at
the start of a session heading into that stage.

Run `/ds-learn` to capture your own project-local lesson (what broke, what
fixed it) — it's appended to `.last-ds-mile/learnings.jsonl` and resurfaces
the same way: automatically, at the start of your next session, if it's
tagged to the stage you're about to work on. See the `capturing-learnings`
skill for what's worth capturing.

## Development

Tooling is [uv](https://github.com/astral-sh/uv) + [ruff](https://github.com/astral-sh/ruff)
+ [prek](https://github.com/j178/prek), configured in `pyproject.toml`.

    uv sync --group dev          # core + test deps, seconds
    uv run pytest                # 210 passed, 7 skipped
    uv run ruff check .

The 7 skips are the Build-loop tests that need AutoGluon. It is an **optional
extra**, not a core dependency — `sealed_bet` imports it lazily, so the
seal/score/contract path never pays for a multi-GB install. To run the full
suite and reproduce `benchmarks/`:

    uv sync --group dev --extra benchmarks   # minutes
    uv run pytest                            # 217 passed

Git hooks (ruff, whitespace, large-file guard):

    uv tool install prek && prek install

`sealed_bet` itself needs only Python >=3.10 with numpy/pandas/scikit-learn.
The `benchmarks` extra is what pins the dev interpreter to 3.13 (see
`.python-version`): AutoGluon's `pyarrow` dependency still has no prebuilt
wheel for 3.14.

`tests/test_plugin_structure.py` validates plugin structure (frontmatter, required
sections, command↔skill wiring, lesson citations); `tests/test_hooks.py`
unit-tests the runtime hooks' actual behavior via subprocess.
