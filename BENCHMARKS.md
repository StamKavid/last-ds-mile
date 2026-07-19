# BENCHMARKS.md — What Dogfooding Found

Two real Kaggle-style benchmarks — `benchmarks/house-prices/` (regression, Ames Housing)
and `benchmarks/telco-churn/` (classification, IBM Telco Customer Churn) — were run
through the full `/ds-frame` → `/ds-handoff` pipeline, using the Sealed Bet mechanism
(`sealed_bet/`) for modeling. Running the plugin against real data surfaced product gaps
that reading the code alone didn't. This file is the durable record of what was found,
what got fixed, and what's still open — every stage doc in both benchmark runs points
here rather than repeating this list inline.

## Fixed

**The ship gate's σ was the wrong statistic.** `sealed_bet.score.open_seal()` computed σ
from the model's own score variance in isolation (`bootstrap_sigma`) — the uncertainty in
"how good is my model?", not "is my model better than the baseline, or did I get lucky?".
That second question needs the σ of the *paired* difference between the model's and
baseline's scores on the same held rows. Fixed via
`sealed_bet.metrics.paired_bootstrap_sigma`, which resamples both predictors together so
shared row-level difficulty cancels out of the delta instead of inflating it. See
`tests/test_metrics.py`'s `test_paired_bootstrap_sigma_is_tighter_than_unpaired_when_errors_are_shared`.

**The baseline was never a real rival.** `seal()` only supported a flat constant
(median/mean) baseline. For `roc_auc` specifically, a constant prediction has no ranking
power, so it scores exactly **0.5 on every classification dataset by construction** — a
"27σ lift over baseline" was really "27σ better than a coin flip," which every
non-broken model clears. Both this run's `04-baseline.md` stages had already *named* a
real non-ML heuristic (neighborhood $/sqft; per-`Contract`-type churn rate) but never
scored it. Fixed via `seal(baseline_fn=...)` / `--baseline-py path:function`, which lets
that heuristic become the Contract's actual baseline. Re-running both benchmarks against
their real heuristics dropped the reported lift from 26.4σ→9.46σ (house prices) and
27.3σ→11.68σ (telco) — smaller, and far more meaningful. See `sealed_bet/seal.py`,
`benchmarks/house-prices/baseline.py`, `benchmarks/telco-churn/baseline.py`.

**Both adversary probes crashed on every real dataset.** `split_adversary` and
`leakage_adversary` (`sealed_bet/adversary.py`) called sklearn models directly on raw
DataFrame columns — the first categorical column (`could not convert string to float:
'Male'`) or the first `NaN` (Ames' `LotFrontage`/`GarageYrBlt`) raised, and the seal
caught the exception and logged "probe skipped." Neither probe had ever successfully run
on a realistic tabular dataset before this fix. Fixed with dtype-aware encoding: ordinal
encoding + median-impute for `split_adversary`'s multi-feature RandomForest (fine for a
tree ensemble judging many features jointly), one-hot encoding for
`leakage_adversary`'s single-feature Logistic/Linear probe (an ordinal code forces an
arbitrary total order onto a nominal column, and a linear model can only see a monotonic
relationship along that order — it would miss a real leak whose category-to-target
mapping doesn't happen to sort that way; proven by
`tests/test_adversary.py::test_leakage_adversary_catches_a_categorical_bijection_a_linear_probe_would_miss`,
which constructs exactly that case and shows the fix catches it).

**`leakage_adversary` was dead code.** It existed, had 9 passing tests, and was never
called from `seal()`. Fixed: `seal()` now runs it and logs a `## Probe
(leakage-adversary, warn-only)` section to the ledger. **Correction made during a later
re-check, worth being precise about:** this does *not* mean the automated probe would
have caught house-prices' `SaleCondition` finding — verified directly:
`leakage_adversary` scores `SaleCondition`'s solo predictive power at R²=0.123, far below
the 0.95 flag threshold, so it would report CLEAR either way. `SaleCondition` was never a
*statistical* leak (a feature that's nearly a copy of the target) — it was a
*known-at-prediction-time* violation (a real, modestly-predictive field that describes
the sale itself and simply wouldn't exist yet at the moment a list price is suggested).
No solo-predictive-power threshold catches that class of problem; it requires domain
reasoning about the decision's timeline, which is what actually caught it in
`03-prep.md`. `leakage_adversary` does its own, different, real job — catching a feature
that's essentially the target in disguise — and now it actually runs, which is the fix;
it was never going to be the fix for the `SaleCondition` class of finding, and claiming
otherwise would overstate what it does.

**`open_seal()` had no sanctioned way to return held-set data for post-hoc analysis.**
`/ds-evaluate` and `/ds-explain`'s own `SKILL.md` instruct producing a slice table,
calibration check, and feature importance "on the held set" — but `open_seal()` only
ever returned an aggregate `{sealed_score, baseline, sigma, lift, shipped}` dict, and a
seal can only be opened once. There was no path back to the held labels once `/ds-open`
had run, which means whoever produced the slice/calibration/importance numbers in the
original two benchmark runs must have gone around the guard to get them. Fixed:
`open_seal()` now calls `sealed_bet.score.reveal()`, which writes `held/revealed.csv`
(the true target plus the submitted predictions) as soon as the seal is opened —
legitimate because the one-look guarantee has already been spent by that point.
`reveal()` refuses to run if the seal isn't opened yet, and also works standalone to
backfill an already-opened seal (used to regenerate both benchmarks' `07-evaluate.md`/
`08-explain.md` honestly, from real data, instead of carrying over unverified numbers).
`held/revealed.csv` is deliberately *not* under the `_sealed*` naming pattern
`seal_guard.py` blocks, so it's readable by the ordinary Read tool once written. See
`skills/ds-evaluate/SKILL.md` and `skills/ds-explain/SKILL.md` for the updated,
concrete instructions.

**`.last-ds-mile/` was blanket-`.gitignore`d.** Every skill hardcodes
`.last-ds-mile/stages/*.md` as its output path, and `sealed_bet`'s own CLI defaults to
`--out .last-ds-mile`. But the root `.gitignore` ignored the whole directory, meaning no
project following the documented workflow could ever commit its own stage docs or
Contract without a workaround — which is exactly why these two benchmark runs live under
`last-ds-mile-run/` (no leading dot) instead. Fixed: `.gitignore` now scopes the ignore
to the heavy/regenerable subpaths only (`dev.csv`, `held/`, `auto/`, `seal_state.json`,
`preds.csv`), matching the pattern `benchmarks/*/last-ds-mile-run/` already used. New
projects can use `.last-ds-mile/` directly and get committable evidence out of the box;
these two historical runs keep their `last-ds-mile-run/` naming unchanged rather than
churn already-committed history for no functional benefit.

**A Windows console crashed printing the verdict.** Both `sealed_bet.seal`'s and
`sealed_bet.score`'s CLI `main()` printed `σ`/`→`, which raised `UnicodeEncodeError` on
Windows' default `cp1252` console codepage — discovered when `python -m
sealed_bet.score --preds ...` crashed *after* successfully opening a seal and writing the
verdict to `LEDGER.md`, i.e., every side effect completed correctly and only the
human-facing summary line failed. Fixed with `sys.stdout.reconfigure(encoding="utf-8")`
in both `main()`s.

**`sealed_bet` only supported `rmse` and `roc_auc`.** For telco's retention-targeting
decision specifically, AUPRC (precision-recall) is more decision-relevant than ROC-AUC
under a 26.5% positive rate — the team cares about how many of the accounts it spends
outreach budget on are genuine churners, which AUPRC captures more directly. Fixed:
`sealed_bet.metrics.METRICS["auprc"]` added. Unlike `roc_auc`'s constant baseline (always
exactly 0.5), AUPRC's constant baseline converges to the positive-class prevalence — a
real, dataset-specific floor rather than a universal number, so it stays meaningful even
without a `baseline_fn`. See
`tests/test_metrics.py::test_auprc_constant_baseline_converges_to_prevalence_not_a_universal_number`.

**`sealed_bet.splits.split(strategy="random")` had no stratification option.** Telco's
26.5% churn rate was moderate enough that an unstratified random split verified
non-fatal after the fact (held-set churn rate 26.1% vs. dev-set 26.6%), but this was a
real, current limitation for the queued `benchmarks/credit-card-fraud/` run: at 0.17%
positive rate, an unstratified split risks a held set with too few (or zero) positives to
score meaningfully. Fixed: `sealed_bet.splits.split(stratify_col=...)`, and a new
`auto_stratify_col(task, strategy, target)` policy function that both `seal()` and
`run_iteration()`'s internal outer split now call — centralizing the "when do we
stratify" decision in one place rather than each site guessing independently (the same
kind of inconsistency that produced the `.last-ds-mile/` vs `last-ds-mile-run/` split
elsewhere in this project). Classification + `random` split now stratifies by the target
automatically; `group`/`time` strategies reject a `stratify_col` outright rather than
silently ignoring it, since they're already partitioned by entity/chronology.

**The split-adversary probe's "SUSPECT" verdict didn't distinguish split strategies.**
`split_adversary` certifies that dev and held are statistically indistinguishable — the
right check for a `random`/`group` split. For a deliberate `time` split (house prices),
dev and held are *supposed* to look different (held is always strictly later), so the
probe firing "⚠ SUSPECT" there (train-vs-held AUC 0.887, lift 35.3σ) was an expected false
positive, not a leak. Fixed: `seal()` now skips the probe entirely for `strategy="time"`
and logs a `## Probe (split-adversary, N/A for this split strategy)` section explaining
why, instead of computing and displaying a number that doesn't mean what its own wording
claims.

**`seal()` always built `feature_cols` as every non-target column, with no way to
exclude a `time_col` from the model's own inputs.** Fine for house prices specifically —
`sale_period` (the time-split key) is itself legitimately known at prediction time, not
an outcome-of-the-sale field. But a future `time_col` that *shouldn't* be a model input
(a raw future-looking timestamp with no standalone predictive legitimacy) would have been
fed to the model anyway, silently. Fixed: `seal(exclude_from_features=[...])` /
`--exclude-from-features col1,col2` drops those columns from `dev.csv`/`held/features.csv`
themselves (not just from a local `feature_cols` variable), so they can never leak into
modeling regardless of how a downstream caller re-derives its own feature list — and
records them in the Contract's new `excluded_features` field for transparency.

**Per-stage outputs were prose-only — no exported figures, and SHAP was optional ("or")
rather than required.** `ds-explore`, `ds-evaluate`, and `ds-explain`'s `SKILL.md`s never
instructed exporting a plot, and `data-viz-standards` (the skill that would have told them
how) was never referenced by any of them — an orphan skill nobody's workflow actually
triggered. `ds-explain`'s own description offered "feature importance, SHAP values, or
partial dependence," and the `or` meant SHAP never happened in practice; permutation
importance was always the cheaper path taken. Fixed: both benchmarks now have a
`figures/` directory (`02-target-distribution.png`, `02-top-correlations.png` /
`02-churn-by-contract.png`, `02-tenure-relationship.png`, `07-slice-performance.png`,
`07-calibration.png` (telco), `08-feature-importance.png`, `08-shap-summary.png`,
`08-hypothesis-dag.png`), generated by committed, reproducible scripts
(`benchmarks/*/generate_figures.py`) rather than one-off throwaway code. SHAP is
computed by explaining the actual shipped ensemble's `predict`/`predict_proba` as a
black-box callable via `shap.Explainer` — not a specific base learner's internals, which
turned out to be fragile to reach into directly (AutoGluon's per-model preprocessing
rejected a NaN-containing category column even after the public `transform_features()`
call; explaining the real `predict()` sidesteps this and is more honest about what ships
anyway). Feature importance is now cross-checked against the best single base learner
(via AutoGluon's own `feature_importance(model=...)` API) alongside the ensemble's — a
real, informative comparison in both benchmarks, not decoration: house-prices' CatBoost
alone assigns near-zero importance to `Neighborhood`/`GarageCars` where the ensemble
doesn't (that signal comes through the other base models entirely), while telco's
CatBoost assigns systematically *higher* importance to nearly every feature than the
blended ensemble does (each feature's marginal contribution shrinks once other models
capturing overlapping signal are blended in) — two different, genuine findings a
single-model view would have missed. `data-viz-standards`' library table now has an
entry for committed static evidence (matplotlib, including SHAP's own plots) alongside
its existing Altair/Plotly/`great_tables` guidance for interactive/stakeholder contexts.
"Causal" was initially scoped to a lite hypothesis-DAG (a diagram of `02-explore.md`'s
already-logged reasoning, not a fitted causal model) after checking a real
causal-inference library (difference-in-differences, `igerber/diff-diff`) against both
datasets: DiD needs a treatment/control assignment and pre/post periods, and neither
benchmark — both single-snapshot prediction problems — has that structure. **Revised**
after reconsidering with two libraries built for purely cross-sectional observational
data instead: [DoWhy](https://github.com/py-why/dowhy) (ATE + refutation) and
[CausalML](https://github.com/uber/causalml) (CATE/heterogeneous effects) don't need a
panel or pre/post structure — just a treatment, an outcome, and a defensible confounder
set. Telco has a natural fit (does signing a long-term contract *cause* lower churn, or
is that confounding by who chooses long contracts?) that maps directly onto the
retention decision `00-frame.md` already frames; built a real analysis —
`benchmarks/telco-churn/causal_analysis.py` /
[`benchmarks/telco-churn/CAUSAL_ANALYSIS.md`](benchmarks/telco-churn/CAUSAL_ANALYSIS.md)
— finding the naive −36pp association is ~60% confounding (causal ATE −14pp, surviving
placebo/random-common-cause/data-subset refutation), with the true effect 2–3× larger
for new and fiber-optic customers specifically. House prices did *not* get a symmetric
analysis: no treatment variable maps onto its framed decision (a list-price *prediction*,
not an intervention) without first reframing `00-frame.md` into a different product.

**`open_seal()` joined predictions to held rows purely positionally, with no identity
check.** `pd.read_csv(preds_path).iloc[:, 0]`. Row *count* was checked
(`len(preds) != len(y_true)` raises), but nothing verified the *order* matched
`held/features.csv`. A prediction pipeline that sorted, reindexed, or otherwise
reordered rows before writing `preds.csv` would silently score against the wrong labels
— no error, just a wrong sealed score with no way to detect it after the fact. For a
tool whose whole purpose is refusing to trust an unearned number, a silent-wrong-answer
path was the worst available failure mode. Fixed: `seal()` now writes
`held/row_ids.csv`, `preds.csv` must echo a `row_id` column, and
`sealed_bet.score._read_predictions` reindexes into held order — raising on a missing
id, an unexpected id, or a duplicate, rather than scoring anyway. The order of
`preds.csv` is now irrelevant. `row_id` lives in its own file rather than as a column of
`features.csv` on purpose: an id column is a row-order proxy, and on any sorted dataset
that is itself a leakage vector, so a leakage-prevention tool must not ship one inside
the feature matrix. Seals written before `row_ids.csv` existed still open positionally,
and `--unsafe-positional-join` restores the old behavior explicitly. Proven by
`tests/test_score.py::test_shuffled_preds_would_have_scored_wrong_under_positional_join`,
which shows perfect predictions collapsing toward chance under the old join, alongside
`test_shuffled_preds_score_identically_when_row_ids_are_carried`, which shows shuffling
is now a no-op.

**The split-adversary probe did not scale, and on a large dataset it dominated the
run.** Found by the third benchmark (`benchmarks/credit-card-fraud/`, 284,807 rows).
With `strategy="random"` the seal took **27m38s**; the identical pipeline with
`strategy="time"`, where the probe is skipped by design, took **2m47s**. The AutoGluon
fit itself was ~2m46s — so a *warn-only diagnostic* was costing roughly 10× the model it
exists to protect, with no progress output and no way to skip it. A user running
`/ds-seal` on a few-hundred-thousand-row dataset (entirely normal in production DS)
would reasonably conclude the tool had hung. Cause:
`cross_val_predict(RandomForestClassifier(n_estimators=100), cv=5)` over every row — 500
trees on ~228k rows each — followed by a 1000-resample `roc_auc` bootstrap over all
284,807. None of those constants scale with anything the user chose; they were fine at
Ames' 1,460 rows and Telco's 7,043 and pathological here. Fixed with
`sealed_bet.adversary.PROBE_MAX_ROWS` (50,000) and a seeded, stratified subsample —
stratified because the dev/held ratio is the very thing the probe measures. Measured on
this dataset's own random split: **284,807 rows / ~25 min / AUC 0.4990 / σ 0.0013 /
CERTIFIED** became **50,000 rows / 178 s / AUC 0.4930 / σ 0.0032 / CERTIFIED** — same
verdict, ~8× faster, with σ honestly widening to reflect the smaller sample. The row
count is written into the Ledger line whenever the cap bites, so a reader always knows
how many rows a verdict rests on rather than the subsampling being invisible.

**The leakage-adversary false-positives on legitimately strong features — and that
completes the picture of what it can tell you.** Both credit-card-fraud variants flagged
`⚠ SUSPECT` on `V14` (solo_score 0.9513 / 0.9529, just over the 0.95 threshold). This is
not leakage: `V1..V28` are PCA components computed *unsupervised* over transaction
attributes and never saw the `Class` label, so a component solo-predicting fraud at 0.95
AUC is genuine discriminative power in a dataset whose design concentrates signal into a
few components. Read against the house-prices `SaleCondition` finding above, this bounds
the probe from both directions: there it reported CLEAR (R²=0.123) on a real
known-at-prediction-time violation; here it reports SUSPECT on a non-violation. The
probe detects exactly one thing — a feature that is nearly a copy of the target — and
cannot distinguish strong legitimate signal from a leak, nor catch a timeline violation
at all. Both verdicts require a human reading them, which is why it is warn-only. Not
"fixed" (there is nothing to fix); recorded so the threshold is not mistaken for a
verdict.

## Open — not fixed here

**The Build loop rejects nearly everything after iteration 1, in every run so far.**
Flagged in the very first review of this repo but never written down here until this
re-check surfaced it was missing. Across every re-seal of both benchmarks (four house-
prices runs, three telco runs, all logged in their respective `LEDGER.md`s), the pattern
is identical: iteration 1 (the full feature set) wins, and every subsequent
feature-drop/engineer attempt is rejected as "within the noise floor." At held-set sizes
of ~290 (house prices) and ~1,400 (telco) rows, `bootstrap_sigma`'s noise floor is
plausibly just larger than any single feature-ablation's effect on `dev_score` — meaning
the Ladder isn't detecting "this change didn't help," it may be structurally incapable of
detecting *any* modest improvement at this sample size, full stop. Not a bug exactly, but
worth knowing before reading "5 rejections, early-stopped" as evidence the search was
thorough: it may equally mean the acceptance criterion can't resolve anything smaller than
a large effect, regardless of how many iterations run.

**`Contract.input_mode` is write-only.** Stored on every Contract, printed in every
`LEDGER.md` header, never read or branched on anywhere in `sealed_bet`. Vestigial —
either give it a real purpose or remove it.

**AutoGluon's own internal model search isn't seeded.** `sealed_bet.auto._fit_predictor`
threads a seed through the outer train/val split and `bootstrap_sigma`, but
`TabularPredictor` itself exposes no top-level seed — real seeding would mean per-model
hyperparameter overrides that differ across LightGBM/XGBoost/CatBoost/etc., a larger
change than this module's scope. In practice, re-running both benchmarks after the fixes
above reproduced the sealed score to 4 decimal places both times — reassuring
empirically, but `10-handoff.md`'s "reruns cleanly" claim shouldn't be read as a
bit-for-bit reproducibility guarantee.

**No slice-adjusted or comparative reporting against Kaggle's public leaderboard beyond
a single human-provided ceiling estimate.** Both reports compare the sealed score to a
`ceiling_score` (human-provided for house prices and telco, informed by community
consensus on "genuinely honest, not overfit-to-public-test" ranges) rather than the raw
public leaderboard, which is widely understood in both communities to include
leaked/overfit submissions after years of test labels being effectively public. This is
a deliberate framing choice (see both `00-frame.md`s), not a gap, but it means "beats the
leaderboard" claims from either dataset's community should not be read as this
benchmark's claim.
