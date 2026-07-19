# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] — first public release

### Fixed

- **Predictions are joined to sealed labels on `row_id`, not row position.**
  `open_seal()` previously matched `preds.csv` to the holdout purely by row
  order; the row *count* was validated but the *order* never was. Any pipeline
  that sorted, grouped, or reindexed before writing predictions scored against
  the wrong labels silently — no error, just a confidently wrong ship/no-ship
  verdict written irrevocably to the Ledger. `seal()` now writes
  `held/row_ids.csv`, `preds.csv` must echo a `row_id` column, and mismatched,
  missing, or duplicated ids raise instead of scoring. `row_id` lives in its own
  file rather than in `held/features.csv`, because an id column is a row-order
  proxy and would be a leakage vector inside the feature matrix. Seals written
  before this still open positionally; `--unsafe-positional-join` restores the
  old behavior explicitly.
- `sealed_bet/state.py` lost the original exception when reporting a corrupted
  seal-state file (missing `raise ... from`), hiding the underlying cause during
  exactly the diagnosis that needed it.
- `/ds-auto` instructed writing a single-column `preds.csv`, which `/ds-open`
  no longer accepts.
- **The split-adversary probe no longer dominates the run on large datasets.**
  On the 284,807-row fraud benchmark it took 27m38s against a 2m47s model fit —
  a warn-only diagnostic costing ~10× the model it protects, with no progress
  output and no way to skip. It cross-validated a 100-tree RandomForest over
  every row, then bootstrapped `roc_auc` 1,000× over all of them. Capped via
  `PROBE_MAX_ROWS` (50,000) with a seeded stratified subsample: same verdict,
  ~8× faster, and the row count is recorded in the Ledger so the cap is never
  invisible.

### Added

- **`pyproject.toml` with a split dependency surface**, replacing
  `requirements-dev.txt`. `sealed_bet`'s core needs only numpy/pandas/
  scikit-learn; AutoGluon (imported lazily) moves to an optional `benchmarks`
  extra with shap/matplotlib. `uv sync --group dev` is now a seconds-long setup
  instead of a multi-GB one, and the core supports Python >=3.10 — the <3.14
  ceiling belongs to the extra, not the package.
- **CI** (`.github/workflows/ci.yml`): ruff, pytest on 3.10/3.12/3.13, a
  dedicated AutoGluon job so the Build-loop path is still covered despite being
  skipped in the lean install, and a SkillSpector security gate.
- **SkillSpector integration.** [NVIDIA SkillSpector](https://github.com/NVIDIA/skillspector)
  scans the plugin on every push and gates CI, with every accepted finding
  justified in `.skillspector-baseline.yaml`. Result: 0/100 with 31 findings
  suppressed — the README states the suppression count rather than the bare
  score, and notes that no NVIDIA verification programme exists.
- **A scope statement in the README**: tabular supervised learning only; the
  pipeline ends at handoff with no deployment/serving/monitoring; and the Sealed
  Bet's guard gates the `Read` tool only, so `Bash`/`Grep` can still reach a
  sealed file — friction, not a sandbox.
- ruff (lint) and prek (`.pre-commit-config.yaml`) for git hooks.
- A test asserting the version string matches across `plugin.json`,
  `package.json`, and `pyproject.toml`.
- **A third benchmark: credit-card fraud** (284,807 rows, 0.173% positives),
  exercising `auprc` and `auto_stratify_col` on the imbalance they were built
  for. Run under *both* split strategies to test whether a random split inflates
  the score on time-ordered data. It did not — the predicted result failed to
  reproduce, and `benchmarks/credit-card-fraud/REPORT.md` says so plainly rather
  than reframing it. See also the leakage-adversary false positive on `V14`,
  which bounds what that probe can detect.

### Changed

- **`/ds-auto` no longer implies its search was exhaustive.** Across all seven
  re-seals of the committed benchmarks, iteration 1 wins and every later
  iteration is rejected as within the noise floor — the Ladder may be
  structurally unable to resolve modest gains at these dev-set sizes. The
  command now states up front that it demonstrates the Ladder rather than
  performing a thorough search, and must report its resolution floor in metric
  units.
- `conftest.py` removed; `[tool.pytest.ini_options] pythonpath` replaces it.
- `data/` is gitignored — raw datasets were previously untracked but uncovered
  by the ignore rules, so `git add .` would have committed them.

### Known limitations

- `seal_guard.py` gates the `Read` tool only. `Bash`/`Grep` are not gated.
- SkillSpector's `SC4` dependency check is not version-aware: it reports every
  OSV advisory for a package name regardless of the version declared. Verified
  by raising floors to current releases and re-scanning — identical findings.
  Every project depending on the standard DS stack scores 100/100 there.
- AutoGluon's internal model search is not seeded; reruns reproduce scores
  closely but not bit-for-bit.

[Unreleased]: https://github.com/stamkavid/last-ds-mile/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/stamkavid/last-ds-mile/releases/tag/v0.2.0
