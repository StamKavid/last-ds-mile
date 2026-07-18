# PUBLISH_PLAN.md — Road to v0.2.0 (first public release)

Working document. Delete or `.gitignore` after the release ships.

**Current state:** 217 tests pass, 20 skills, 16 commands, 5 audited hooks, 3 subagents,
2 completed benchmark runs. Structurally strong; three classes of gap remain.

**Release gate:** everything in P0 is done, and no P1 item is half-finished in a way that
makes a claim the repo can't back.

---

## Priority key

| Tier | Meaning |
|---|---|
| **P0** | Blocks publishing. Either a correctness bug, or a claim the repo makes that isn't true. |
| **P1** | Credibility. The package works without these, but a skeptical DS bounces off. |
| **P2** | Depth. Do after v0.2.0 ships and real users show up. |

---

# P0 — Blocks publishing

## P0-1. Toolchain migration: uv + ruff + prek + pyproject.toml

**Why P0:** `requirements-dev.txt` mixes a 2 GB AutoGluon install into what should be a
seconds-long contributor setup, and there is no linter at all in a repo that will be read
as a reference implementation. Both are visible on first contact.

### Delete
- `requirements-dev.txt`
- `conftest.py` — its only job is putting the repo root on `sys.path`, which
  `[tool.pytest.ini_options] pythonpath = ["."]` does natively.

### Create `pyproject.toml`

```toml
[project]
name = "last-ds-mile"
version = "0.2.0"
description = "A guided data-science lifecycle for Claude Code, with leakage and honesty checks built into every stage."
readme = "README.md"
license = { file = "LICENSE" }
authors = [{ name = "Stamatis" }]
requires-python = ">=3.10"
keywords = ["data-science", "machine-learning", "eda", "validation", "leakage", "mlops", "skills"]

# sealed_bet core only. Verified against actual imports:
# adversary/metrics/splits use sklearn; contract/ledger/state are stdlib.
dependencies = [
    "numpy>=1.26",
    "pandas>=2.0",
    "scikit-learn>=1.4",
]

[project.urls]
Homepage = "https://thelastaimile.substack.com"
Repository = "https://github.com/stamkavid/last-ds-mile"

[project.optional-dependencies]
# Only needed to REPRODUCE benchmarks/. AutoGluon is imported lazily inside
# sealed_bet/auto.py::_fit_predictor, so the core never pays for it.
# AutoGluon's pyarrow dep has no 3.14 wheel yet -> this extra is the reason
# for the <3.14 practical ceiling, NOT the core package.
benchmarks = [
    "autogluon.tabular[lightgbm,catboost,xgboost]>=1.5.0",
    "matplotlib>=3.8",
    "shap>=0.44",
]
causal = [
    "dowhy>=0.11",
    "causalml>=0.15",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "PyYAML>=6.0",          # tests/test_plugin_structure.py parses SKILL.md frontmatter
    "ruff>=0.9",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["sealed_bet"]

[tool.pytest.ini_options]
pythonpath = ["."]          # replaces conftest.py
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py310"
extend-exclude = [".venv", "benchmarks/*/last-ds-mile-run", ".last-ds-mile"]

[tool.ruff.lint]
select = [
    "E", "W",    # pycodestyle
    "F",         # pyflakes
    "I",         # isort
    "UP",        # pyupgrade
    "B",         # bugbear
    "SIM",       # simplify
    "RUF",
]
ignore = ["E501"]   # line length is handled by the formatter

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["B011"]
```

### Create `.python-version`
```
3.13
```
Pins the default dev interpreter (AutoGluon still lacks 3.14 wheels).

### Create `.pre-commit-config.yaml` (run by **prek**, the Rust runner)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-json
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=2048]   # keeps model binaries / CSVs out of git
```

`prek` is a drop-in pre-commit replacement and reads this file unchanged.
Install: `uv tool install prek && prek install`.

### Rewrite the README Development section

```bash
uv sync --group dev                    # seconds — core + test deps only
uv run pytest                          # 217 tests
uv run ruff check . && uv run ruff format --check .

uv sync --group dev --extra benchmarks # minutes — only to reproduce benchmarks/
uv tool install prek && prek install   # git hooks
```

### Acceptance
- [ ] `uv sync --group dev` completes without pulling AutoGluon
- [ ] `uv run pytest` → 217 passed
- [ ] `uv run ruff check .` → clean (expect a real first-pass fix list; do not `--fix` blindly through `sealed_bet/`)
- [ ] `conftest.py` and `requirements-dev.txt` are gone
- [ ] `uv.lock` committed

---

## P0-2. CI (missing entirely)

**Why P0:** a plugin that others `npx`-install with zero CI is an unverifiable claim.
`.github/workflows/` does not exist today.

`.github/workflows/ci.yml` — on push + PR:
1. `astral-sh/setup-uv@v5`
2. `uv sync --group dev`
3. `uv run ruff check .` / `uv run ruff format --check .`
4. `uv run pytest` (matrix: 3.10, 3.12, 3.13)
5. `uv run pytest tests/test_plugin_structure.py tests/test_hooks.py` explicitly named in
   the job summary — these are the two that protect plugin consumers

Add the build badge to the README. **Do not** add a badge until the workflow is green.

---

## P0-3. Fix the positional prediction join

**Why P0:** this is the one open bug that directly contradicts the product thesis.
`open_seal()` matches `preds.csv` to sealed labels by row position only
([sealed_bet/score.py:78](sealed_bet/score.py:78)); row *count* is validated, order is not.
Any pipeline that sorts or reindexes before writing predictions scores against the wrong
labels — silently, with no error, producing a confidently wrong verdict.

Shipping an honesty tool with a silent-wrong-answer path is the worst available bug.

**Fix:** write a `row_id` column into `held/features.csv` at seal time; require `preds.csv`
to echo it; join on it and raise on any mismatch. Keep a legacy positional path behind an
explicit `--unsafe-positional-join` flag so existing sealed runs still open.

**Tests:** shuffled `preds.csv` raises; correctly-keyed out-of-order `preds.csv` scores
identically to in-order.

---

## P0-4. Tell the truth about `/ds-auto`'s search

**Why P0:** [BENCHMARKS.md](BENCHMARKS.md) already documents that across all 7 re-seals,
iteration 1 always wins and every later iteration is rejected as "within the noise floor" —
the ladder may be structurally unable to resolve any modest gain at these sample sizes.
A user reading "5 rejections, early-stopped" will conclude the tool searched thoroughly.
It didn't; it may be blind.

**Minimum:** `/ds-auto` prints its own resolution floor before iterating
("at n=290 held rows, σ ≈ X; changes smaller than 2σ ≈ Y are undetectable"), and
`commands/ds-auto.md` + README label it a demonstration of the mechanism, not a search.

**Better (do if time allows):** switch the ladder's acceptance from a single dev-score
delta to repeated CV, which actually buys resolution.

---

## P0-5. Scope statement in the README

One paragraph near the top, because all three are currently implied rather than stated:
- **Tabular supervised learning only** — no text, vision, or time-series forecasting
- **The pipeline ends at handoff/packaging** — no deployment, serving, monitoring, or drift
- **The Sealed Bet is experimental**, and `seal_guard` gates the `Read` tool only;
  `Bash`/`Grep` can still reach a sealed file. It is friction, not a sandbox.

The third point is already honest in [AUDIT.md](AUDIT.md); it needs to be equally
prominent wherever the Sealed Bet is *sold*, not only where it's audited.

---

# P1 — Credibility

## P1-1. Run the third benchmark (credit-card-fraud)

**Blocker for P1-2.** `benchmarks/credit-card-fraud/` currently holds only
`creditcardfraud-metadata.json`. There is no run. A README section claiming three datasets
would be false today.

This is also the run the codebase was already prepared for: `auto_stratify_col` and the
`auprc` metric were both added specifically because a 0.172% positive rate breaks an
unstratified split and makes ROC-AUC misleading. Running it validates those two fixes on
the case they were built for.

Setup:
- metric: **`auprc`** (the dataset's own authors recommend AUPRC over accuracy)
- split: `random`, auto-stratified by `Class`
- real heuristic baseline: an `Amount`-threshold or a single-`V`-feature rule —
  **not** a constant, so the baseline is a genuine rival
- expect the constant-AUPRC floor ≈ 0.0017 (prevalence), which is exactly why AUPRC was
  chosen over ROC-AUC's universal 0.5

Full `/ds-frame` → `/ds-handoff`, committed the same way as the other two.

## P1-2. README results section — framed so it survives scrutiny

**The trap:** both existing reports deliberately compare to a *human-estimated honest
ceiling*, not the public leaderboard, because both leaderboards are understood to contain
leaked/overfit submissions. And [telco's 09-report.md](benchmarks/telco-churn/last-ds-mile-run/stages/09-report.md)
explicitly says to treat its numbers as "illustrative of the mechanism working correctly,
not as a permanent, citable score."

A naive "Last DS Mile vs Kaggle leaderboard" table would contradict your own documentation
and hand a reviewer the exact stick to beat you with. Frame it as *what one honest,
reproducible run produced*, with the ceiling as context.

Verified numbers currently in the repo:

| Dataset | Task | Metric | Real heuristic baseline | Sealed score | Lift | Honest ceiling |
|---|---|---|---|---|---|---|
| House Prices (Ames) | regression | RMSE, log scale ↓ | 0.2487 (neighborhood median $/sqft) | **0.1311** | 9.46σ | ~0.115 |
| Telco Churn (IBM) | classification | ROC-AUC ↑ | 0.7420 (churn rate per contract type) | **0.8471** | 11.68σ | ~0.85 (range 0.82–0.86) |
| Credit Card Fraud | classification | AUPRC ↑ | _P1-1_ | _P1-1_ | _P1-1_ | _P1-1_ |

Every number above is already sourced from a committed `contract.json` / `09-report.md` —
do not retype them by hand, and re-derive them if any re-seal happens before release.

Required framing paragraph, roughly:

> These are single honest runs, not leaderboard entries. Each score is measured once,
> on a holdout sealed before modeling began, against a real non-ML heuristic rather than
> a constant. The "honest ceiling" is a human estimate of what each problem is understood
> to top out at *without* overfitting to a years-public test set — we compare against that
> rather than the public leaderboard on purpose. Exact numbers shift slightly between
> re-seals; the point is the mechanism and its reproducibility, not the decimals.

Then the reproduce command, which is what actually makes it credible:

```bash
uv sync --group dev --extra benchmarks
uv run python -m sealed_bet.seal --data ... --baseline-py benchmarks/telco-churn/baseline.py:contract_rate ...
```

Add "what dogfooding found" as the hook into [BENCHMARKS.md](BENCHMARKS.md) — the ~12 real
bugs those runs surfaced are more persuasive than any score.

## P1-3. SkillSpector integration

NVIDIA's [SkillSpector](https://github.com/NVIDIA/skillspector) (Apache-2.0) scans agent
skills for 68 vulnerability patterns across 17 categories and emits a structured verdict:
`risk_score` (0–100), `severity`, `recommendation`, `safe_to_install`, plus SARIF for CI.

**Read this before writing any badge copy:** SkillSpector produces a **risk score where
lower is better**, and there is no NVIDIA verification, certification, or badge program.
"NVIDIA verified" would be an overclaim — and overclaiming is the one thing this project
cannot afford to do, given it sells honesty. Self-report the score, show the command,
let readers reproduce it.

Steps:

1. **Scan locally first, before promising anything publicly:**
   ```bash
   uv tool install git+https://github.com/NVIDIA/skillspector.git
   skillspector scan . --no-llm --format markdown --output /tmp/skillspector.md
   ```
   Expect false positives. This repo legitimately contains things that pattern-match as
   hostile: `hooks/scan_untrusted_input.py` holds literal prompt-injection and shell-magic
   patterns *as detection strings*, and `seal_guard.py` returns a tool-denial decision.
   Triage each finding honestly — do not baseline away anything real.

2. **Baseline the accepted false positives**, and commit it with a comment per entry
   explaining *why* it's accepted:
   ```bash
   skillspector baseline . -o .skillspector-baseline.yaml
   ```

3. **Add to CI** as a separate job, SARIF uploaded to GitHub code scanning:
   ```bash
   skillspector scan . --no-llm --baseline .skillspector-baseline.yaml \
     --format sarif --output skillspector.sarif
   ```
   Static-only (`--no-llm`) in CI keeps it key-free and deterministic. Run the LLM pass
   manually before each release.

4. **README copy — honest version:**
   > **Security scan:** this plugin scans clean under
   > [NVIDIA SkillSpector](https://github.com/NVIDIA/skillspector) (risk score N/100,
   > static analysis, `<commit>`). Reproduce: `skillspector scan .`
   > Accepted false positives are documented in `.skillspector-baseline.yaml`.

   Not "verified." Not "NVIDIA-approved." A number, a date, and a command.

5. Cross-link [AUDIT.md](AUDIT.md) ↔ the scan result. Your hand-written audit plus an
   independent scanner agreeing is a stronger story than either alone — and it is a real
   differentiator, since almost no skill bundle ships either.

**Note the timing risk:** SkillSpector is young and moving fast (286 commits, 44 open
issues). Pin the version you scanned with and re-scan per release rather than treating a
one-time score as permanent.

## P1-4. CHANGELOG.md + version bump

Bump `0.1.0` → `0.2.0` in `.claude-plugin/plugin.json`, `package.json`, and `pyproject.toml`
together (three places — easy to desync; consider a test asserting they match).
Keep-a-Changelog format. The BENCHMARKS.md fix list is most of the 0.2.0 entry already.

---

# P2 — Depth (after v0.2.0)

Ordered by how much each closes the gap between the name and the contents.

1. **`deployment-monitoring` stage/skill.** The package is called *Last DS Mile* and stops
   at packaging. Drift detection, retraining triggers, and monitoring are the actual last
   mile. Biggest single credibility gap.
2. **`time-series-validation` skill.** Time leakage is your most-cited failure mode and it
   lives only in a lesson, not a triggerable skill. Cheapest high-value addition.
3. **`causal-inference` skill.** You already built and validated a real DoWhy/CausalML
   analysis in `benchmarks/telco-churn/causal_analysis.py`. Package what you proved works.
4. **Deepen `/ds-prep` and `/ds-model`.** Your two most craft-heavy stages are your two
   shortest skills. Encoding strategies, target encoding done safely, OOF discipline,
   stacking/blending, HPO. This is the gap a strong DS notices fastest.
5. **`feature-store` / reproducibility hardening** — seed AutoGluon properly, or state
   plainly that reruns are statistically reproducible but not bit-identical.
6. **Close the `seal_guard` Bash/Grep gap**, or formally reclassify the Sealed Bet as
   deterrence rather than enforcement.
7. **Retire `Contract.input_mode`** — write-only, never read, per BENCHMARKS.md.

---

# Suggested sequence

| Step | Work | Rationale |
|---|---|---|
| 1 | P0-1 toolchain | Everything else runs through it |
| 2 | P0-2 CI | Locks in step 1; makes the rest verifiable |
| 3 | P0-3 join fix + P0-4 auto honesty | Correctness before promotion |
| 4 | P1-1 fraud benchmark | Long-running; also exercises the P0-3 fix on a third dataset |
| 5 | P1-3 SkillSpector scan + triage | Findings may force code changes — do before README freeze |
| 6 | P0-5 scope + P1-2 results + P1-4 changelog | README written last, once every claim is backed |
| 7 | Tag v0.2.0 | |

**One rule for step 6:** write the README last. Every sentence in it should point at
something already true in the repo — a passing CI run, a committed contract, a
reproducible scan. That discipline is the product; the README should be built the same way.
