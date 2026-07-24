# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **With/without skill-eval harness (`benchmarks/evals/`)** — a benchmark that runs the
  same task twice (plugin installed vs. not), grades both blind on the *outcome*, and
  reports the reproducible per-expectation gap (pass^k vs pass@k). The `evals.json` and
  `grading.json` schemas and the blind two-arm grader are taken from Anthropic
  `skill-creator`'s eval system; the `pass^k` aggregation, `benchmark.json` shape, and
  HTML viewer are our own and are not compatible with skill-creator's eval-viewer. First eval set is
  6 credit-card-fraud cases (4 positive core-discipline cases, 2 negative-trigger
  guards) exercising the accuracy trap, planted-metric framing, target leakage, and
  test-set peeking. `README.md` maps all ten skill-eval best practices to how the
  harness implements each; `run_eval.py`/`aggregate.py` are stdlib-only.
- **Second eval set + a committed worked example.** `benchmarks/evals/house-prices/`
  adds 6 cases built around the target-leakage trap (a neighbourhood-mean-of-`SalePrice`
  feature) on a skewed regression target. `benchmarks/evals/example/` is a committed,
  graded with/without comparison of eval 1 for both datasets — the `with_skill` arm
  graded against the repo's real shipped benchmark pipelines, the `without_skill` arm a
  committed **reproducible** `naive_run.py` (real numbers: fraud accuracy 0.9995 /
  ROC-AUC 0.944, house-prices in-sample RMSE $11,058 / R² 0.98) — showing a pass^k gap
  of 0.875 (fraud) and 0.80 (house-prices). An HTML eval-viewer renders the comparison.
- **`aggregate.py` also emits `benchmark.skill-creator.json`** in skill-creator's exact
  eval-viewer schema (`runs[]` keyed by `configuration`, nested `result.pass_rate`,
  `run_summary.<config>.pass_rate.{mean,stddev}`), alongside our `pass^k` `benchmark.json`
  — so results are portable to skill-creator's viewer without giving up the `pass^k` view.
- **`/ds-frame` now takes an information inventory** — a framing-time step that writes
  down what will actually be known at prediction time versus what only becomes known
  after the fact, recorded in `00-frame.md`. It's the proactive complement to
  `/ds-prep`'s per-feature "known at prediction time?" check, and it surfaces available
  signal (e.g. prior-period totals) before feature-building instead of after.

### Changed

- **`/ds-frame` and `metric-selection` now treat over- vs under-prediction asymmetry as
  a first-class question.** `metric-selection` gains a regression row for asymmetric cost
  (quantile/pinball loss at a chosen service level) alongside the existing
  classification-only F-beta row; `/ds-frame` asks whether over- and under-shooting cost
  the same before locking a symmetric metric.
- **`/ds-baseline` now warns against strawman baselines** — a global mean/majority on
  data with strong temporal, seasonal, or hierarchical structure is trivial to beat, so
  a too-weak baseline inflates apparent lift. Guidance and a Red Flag now push toward the
  strongest *simple* anchor (last value, same period last cycle, or the rule already in
  use).
- **`/ds-frame` flags forecasting as out of scope when it sees it** — a target that is a
  future value of a time-indexed series now trips a Red Flag pointing at README → Scope,
  stating plainly that these gates aren't a forecasting stack (weak mean baseline, no
  lag/rolling feature machinery) rather than underperforming silently.

## [0.8.0] — the deployment mile: /ds-package and /ds-deploy

### Added

- **`/ds-package` (stage 11)** — wraps a handed-off model behind an inference
  contract and a framework-agnostic predict wrapper, then proves **training/serving
  parity** (the packaged model must reproduce its offline predictions) before it will
  proceed. Emits a reproducible `Dockerfile` (image digest recorded, binary never
  committed). Hard gate on the `/ds-handoff` artifacts. Writes `11-package.md`.
- **`/ds-deploy` (stage 12)** — stands the parity-verified package up as a
  **local-first** callable endpoint, and gates a full-traffic deploy on a monitoring
  hook (predictions logged against the live baseline), a drift hook (reusing the
  `distribution-shift` skill), and a rollback pointer. Any push to a remote/registry/
  cloud target stops and asks — the plugin never pushes to production on its own.
  Writes `12-deploy.md`.

### Changed

- The pipeline now runs `0 → 12`; the `/ds` router, `ds-method` gates/red-flags, and
  the README Commands table and Scope section reflect the deployment mile. The only
  part of the last mile still on the roadmap is automated retraining triggers.
- Skill count 28 → 30; commands 15 → 17; hard gates 3 → 5.

## [0.7.0] — add data-science-project entry-point skill

### Added

- **`data-science-project` entry-point skill** — the auto-triggering counterpart
  to the `/ds` command. Fires when a user starts a tabular ML/DS task in plain
  language ("help me build a churn model", "predict this column") without typing
  `/ds`, and routes them to `/ds-frame` before any data or model is touched. Gates
  on `.last-ds-mile/stages/`: it onboards a cold-start user, and defers to the
  `/ds` router once the pipeline is already underway, so it never re-onboards
  mid-pipeline. Prefix-less (no command, like the domain skills) and scoped tightly
  to avoid over-triggering on non-DS work. Brings the skill count to 28.

## [0.6.0] — fix broken figure links, add /ds-brief for non-technical audiences

### Fixed

- **Every figure link in every benchmark's `07-evaluate.md`/`08-explain.md`/
  `02-explore.md` was broken** — written as `../.last-ds-mile/figures/...` from a
  file already inside `.last-ds-mile/stages/`, adding a nonexistent extra
  `.last-ds-mile/` segment (`stages/` and `figures/` are siblings, not nested).
  This is also why no chart ever rendered inline on GitHub — the figures were
  generated correctly, only the reference to them was wrong. Fixed across all 14
  image references in all three benchmarks; verified every relative link in
  `benchmarks/` and `showcase/` now resolves to a real file.
- Swept all three benchmarks for other staleness (artifact filenames, cross-stage
  number consistency, stray `/ds-iterate` references) — found nothing else wrong.

### Added

- **`ds-brief` skill and `/ds-brief` command** — translates `/ds-report`'s
  technical narrative into a one-page, jargon-free brief for non-technical
  stakeholders (executives, a board, a frontline team lead). No metric names or
  statistical terms permitted; every claim must trace back to `/ds-report` rather
  than introducing new analysis. Demonstrated with real examples for all three
  benchmarks (`09b-brief.md`), each verified jargon-free and under 350 words.
- **`CONTRIBUTING.md`, `SECURITY.md`, `CLAUDE.md`** — contribution workflow, private
  vulnerability reporting, and repo-specific instructions for Claude Code sessions
  working in this codebase.

## [0.5.0] — association is not causation

Found while extending the 0.4.0 benchmarks to two new datasets (telco-churn,
credit-card-fraud) and battle-testing all three across 5 seeds: a real causal-vs-
predictive overreach in the telco-churn benchmark's own EDA writeup ("contract
commitment *reduces* churn... confirmed"), stated from a correlational group
comparison with an unaddressed self-selection confound. Traced across the whole
engagement to confirm it was an isolated instance, not a pattern, then closed the
package-level gap that let it happen: no skill previously distinguished a
predictive/associational finding from a causal one.

### Added

- **`causal-vs-predictive` domain skill** — catches "X reduces/causes/drives Y,
  confirmed" language backed only by a correlational comparison; names
  self-selection as the confound to check first for any feature the subject chose
  themselves (a contract, a plan, an opt-in). Distinguishes ranking/scoring uses
  of a model (need only predictive validity) from intervention recommendations
  (need a causal argument the analysis may not have made).
- **`/ds-explain` step 6** — every driver finding must be worded as predictive/
  associational unless a causal identification strategy is stated.
- **`/ds-report` step 5** — any recommendation implying intervention on a feature
  (not just ranking/scoring with it) is checked against `causal-vs-predictive`
  before shipping.
- **Two new full benchmark builds** (`benchmarks/telco-churn`,
  `benchmarks/credit-card-fraud`), all 11 stages, matching house-prices' treatment:
  frame through handoff, with a frozen deployment threshold, dollar/revenue cost
  translation, and 5-seed reliability checks for both. Both land inside
  independently published reference ranges for their respective datasets.
- **`the-imbalance-knob-that-broke-silently` lesson** — LightGBM's
  `scale_pos_weight` collapsed (PR-AUC 0.04 vs. 0.82+ for every other candidate) at
  credit-card-fraud's ~600:1 imbalance ratio; `class_weight="balanced"` didn't.
  Caught because the comparison table made the outlier visible, not because it was
  anticipated.
- **`the-contract-that-wasnt-the-cause` lesson** — the concrete case behind the new
  skill above.

## [0.4.0] — bias/variance, ensembling, thresholds, cost

Closes the Tier 2/3 items from the same three-lens review behind 0.3.0: the gaps
below the four highest-leverage ones, surfaced when actually rerunning a benchmark
against the 0.3.0 fixes exposed exactly where the method still stopped short.

### Added

- **`model-ensembling` domain skill** — blending/stacking/seed-averaging with
  leakage-safe out-of-fold predictions, evaluated against the best single
  component's fold spread, not just a higher mean. Un-orphans `/ds-explain`'s
  existing ensemble-interpretation guidance, which previously had no stage that
  produced an ensemble to interpret.
- **Bias/variance diagnosis in `/ds-model`** — the winning candidate's train-fold
  score is now compared to its validation-fold score (already available from the
  existing CV loop, no extra training) to diagnose overfitting vs. underfitting and
  point at the right next lever, instead of jumping straight to "try another model."
- **Threshold-freezing step in `/ds-model`** — for classification problems with a
  hard deployment decision, the operating threshold is now chosen on validation
  predictions only and explicitly frozen before evaluation, closing a threshold-as-
  leakage-surface gap the review flagged.
- **Cost-model carry-through in `/ds-report`** — the metric lift is now required to
  be translated into `/ds-frame`'s original business-cost terms at the actual chosen
  operating point (a dollar figure, a rate, a count), not left as a bare metric delta
  stakeholders have to interpret themselves.

### Fixed (found while rerunning the house-prices benchmark against 0.3.0)

- The benchmark run's own modeling script had three real bugs a Kaggle-competitive
  review caught: Ridge/Lasso were fed unscaled, skewed features (their reported
  instability was partly a preprocessing bug, not a finding about linear models);
  CatBoost was one-hot-encoded instead of given native categorical handling; SHAP used
  the slow ensemble-oriented explainer path on a single model, contradicting
  `ds-explain`'s own guidance to use the fast native path for a non-ensemble model.
  All three fixed in `benchmarks/house-prices/scripts/`, which also now includes a
  blended candidate and a light nested-CV tuning pass demonstrating the new skills.

## [0.3.0] — close the loop, quantify the noise

Driven by a three-lens review of the first public release (ML-pedagogy, Kaggle
competitive practice, and enterprise model-risk perspectives independently converged
on the same four gaps). Closes the highest-leverage ones.

### Added

- **`/ds-iterate`** — a new pipeline stage that reads `/ds-evaluate`'s slice table and
  error analysis, diagnoses the specific cause (bias, variance, a slice weakness,
  leakage, or distribution shift), and routes back to the exact prior stage that
  fixes it, or confirms the result is ready for `/ds-explain`. Turns the pipeline
  from a straight line into an explicit, auditable loop
  (`.last-ds-mile/stages/07-iterate-log.md`).
- **`uncertainty-quantification` domain skill** — every CV score reported in
  `/ds-model` and `/ds-evaluate` now carries its fold spread, and every
  model-vs-baseline or model-vs-model comparison states whether the gap exceeds
  that spread. Applies the plugin's own honesty standard to its own numbers.
- **`distribution-shift` domain skill** — adversarial validation and per-feature
  drift checks between training data and a fixed test set or deployment
  population. Wired in as a fourth structural question in `/ds-validate` (alongside
  time, groups, and imbalance) and as a check in `/ds-evaluate`.
- **Protected-attribute slicing in `/ds-evaluate`** — slice performance now
  explicitly covers protected/sensitive attributes (or close proxies) when present
  in the dataset, not only business-convenience segments.

### Changed

- `.gitignore` now excludes raw Kaggle CSVs and heavy model/AutoGluon artifacts
  under `benchmarks/**` (mirroring the existing `.last-ds-mile/` rule), while
  keeping the narrative evidence (`stages/*.md`, `LEDGER.md`, `contract.json`,
  figures) trackable.
- README's "Hard gates, not suggestions" claim softened to match `ds-method`'s
  actual enforcement (warn and stop to ask, never a silent block) — the prior
  wording ("actively refuse to proceed," "structural, not advisory") overstated
  the mechanism relative to this plugin's warn-never-block safety posture.

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

[Unreleased]: https://github.com/stamkavid/last-ds-mile/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/stamkavid/last-ds-mile/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/stamkavid/last-ds-mile/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/stamkavid/last-ds-mile/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/stamkavid/last-ds-mile/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/stamkavid/last-ds-mile/releases/tag/v0.2.0
