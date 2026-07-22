# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/stamkavid/last-ds-mile/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/stamkavid/last-ds-mile/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/stamkavid/last-ds-mile/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/stamkavid/last-ds-mile/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/stamkavid/last-ds-mile/releases/tag/v0.2.0
