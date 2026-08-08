# Benchmarks

Three public datasets, each taken end-to-end through `/ds-frame` → `/ds-handoff` by an
agent running this plugin. They exist for two reasons:

1. **Evidence** that the discipline produces defensible models, not just plausible prose.
2. **Regression tests for skill content.** If a skill's guidance changes in a way that
   would have changed what one of these runs did, the affected stage gets re-run rather
   than assumed still valid.

Every run's full narrative — framing, data audit, EDA, prep, baseline, validation,
modelling, evaluation, explanation, report, handoff — is committed under each dataset's
`.last-ds-mile/stages/`. That's the actual deliverable; the scores below are a summary.

> **What these do *not* show.** There is no control arm here. These runs prove the
> pipeline produces good numbers; they cannot tell you what the *plugin* adds over the
> same model working unaided. That question is
> [open and currently unanswered](../README.md#what-is-not-measured-does-the-plugin-change-the-answer).

---

## The three cases, and why these three

They were picked to cover the three shapes of tabular problem where the discipline
bites differently — not because they're famous.

| | [House Prices](house-prices/) | [Telco Churn](telco-churn/) | [Credit Card Fraud](credit-card-fraud/) |
|---|---|---|---|
| **Task** | Regression | Binary classification | Binary classification |
| **What it stresses** | Skewed target, log-space metrics, small n | Moderate imbalance, threshold choice, cost asymmetry | Severe imbalance, metric traps, PR-AUC |
| **Rows** | 1,460 | 7,043 | 283,726 (284,807 raw, before dedup) |
| **Positive rate** | — | 26.5% | **0.167%** (post-dedup; 0.173% on the raw file) |
| **Primary metric** | RMSE of `log(SalePrice)` | ROC-AUC (PR-AUC secondary) | PR-AUC (average precision) |
| **Kaggle** | [competition](https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques) | [dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) | [dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) |

The fraud set is the one that earns its place hardest: at 0.167% positives, majority-class
accuracy is **99.83%**, which is exactly the number that makes an unaided model declare
victory.

Skill *routing* is checked separately and for free — see [`routing/`](routing/), which
holds a trigger corpus for every skill and the deterministic check that runs in CI.

---

## Results, and how they compare

**Read the comparison column carefully — it is not a leaderboard placement.** Our numbers
are **5-fold cross-validated scores on the training data**. A Kaggle public leaderboard
score is a submission scored against a held-out test set. Those are different quantities
and putting them in the same table would be exactly the kind of apples-to-oranges
comparison this plugin exists to stop. The column below says whether our score lands in
the range independent published work reports *for the same kind of evaluation*.

| Dataset | Shipped model | Our CV score | 5-seed reliability | Independent reference | Verdict |
|---|---|---|---|---|---|
| House Prices | Blend (LightGBM + CatBoost-native) | **log-RMSE 0.1244** ± 0.0141 | mean 0.1228, **seed std 0.0014** | ~0.11–0.13 is competent work on this dataset | In range |
| Telco Churn | Blend (LogReg + CatBoost-native) | **ROC-AUC 0.8477** ± 0.0113 | mean 0.8477, **seed std 0.0004** | ~0.84–0.86 in published kernels (LogReg/XGBoost) | In range |
| Credit Card Fraud | Blend (LightGBM + CatBoost) | **PR-AUC 0.8455** ± 0.0117 | mean 0.8465, **seed std 0.0010** | ~0.85–0.87 for top single models in published analyses | In range |

Lift over the honest baseline, which is the number that actually matters:

| Dataset | Baseline | Model | Lift |
|---|---|---|---|
| House Prices | 0.3999 (mean predictor) | 0.1244 | **3.2× lower error** |
| Telco Churn | 0.5000 (random ranking) | 0.8477 | **+0.348 ROC-AUC** |
| Credit Card Fraud | 0.00167 (= the base rate) | 0.8455 | **506× the no-skill floor** |

### About the House Prices leaderboard specifically

House Prices is the only one of the three that is an actual competition, and **its public
leaderboard is not a usable reference.** The underlying Ames, Iowa housing data is
publicly available in full, so the test-set ground truth is obtainable — the top of the
leaderboard sits at essentially 0.00000, which reflects people submitting the known
answers, not modelling skill. Any comparison against those scores would be meaningless.

This is worth stating plainly rather than quietly picking a friendlier reference: a
leaderboard is only a benchmark if the answers are actually hidden. For a genuine
reference point, published non-leaking work on this dataset lands around 0.11–0.13
log-RMSE, which is the range used above.

Telco Churn and Credit Card Fraud are **datasets, not competitions** — there is no
leaderboard for either. Their reference ranges come from the literature review recorded
in each run's `09-report.md`. Treat them as "consistent with published work," not as a
ranking.

### The finding that didn't flatter the model

The House Prices run's own report ([`09-report.md`](house-prices/.last-ds-mile/stages/09-report.md))
is the best single illustration of what these benchmarks are for:

| Scope | log-RMSE | Typical relative error | Typical $ error |
|---|---|---|---|
| Overall | 0.1244 | 13.2% | ~$21,600 at median price |
| **Cheapest quintile** | **0.1717** | **18.7%** | ~$19,950 at Q1 median |

The framing stage set the bar at an agent's own manual accuracy, roughly 10–15%. Overall
the model lands at 13.2% — inside that band, real help, not a dramatic beat. **On the
cheapest quintile it lands at 18.7%, worse than an experienced agent doing it by eye.**

A run that reported only "beats the baseline by 19.5× its noise" would have been true and
useless. The slice table is what turned it into a deployment decision: don't ship this for
sub-$130k listings.

---

## Reliability and reproducibility, checked rather than assumed

- **Seed stability.** Every score was recomputed across 5 independent CV-splitter seeds.
  In all three cases the seed-to-seed standard deviation is 10–30× smaller than the
  within-run fold-to-fold deviation — the number is a property of the model and data, not
  a lucky split.
- **Independent recomputation.** Each dataset's model-comparison, evaluation, and
  seed-stability scripts were written separately, share only that dataset's
  `pipeline_lib.py`, and were each re-run fresh. Every run agrees with every other to 4
  decimal places, recorded per-dataset in `10-handoff.md`.
- **Pinned environments.** See each folder's `requirements-lock.txt` (house-prices) and
  the versions recorded in `artifacts/model_card_meta.json`.

---

## Reproducing a run

**The datasets are not committed.** This repo never redistributes third-party data, which
also keeps dataset licensing out of scope — see [`.gitignore`](../.gitignore). Download
them first:

| Dataset | Get it | Put it at |
|---|---|---|
| House Prices | [Kaggle competition](https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques) → `train.csv`, `test.csv` | `benchmarks/house-prices/` |
| Telco Churn | [Kaggle dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) → `WA_Fn-UseC_-Telco-Customer-Churn.csv` | `benchmarks/telco-churn/` |
| Credit Card Fraud | [Kaggle dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) → `creditcard.csv` | `benchmarks/credit-card-fraud/` |

With the [Kaggle CLI](https://github.com/Kaggle/kaggle-api) configured:

```bash
cd benchmarks/house-prices
kaggle competitions download -c house-prices-advanced-regression-techniques -f train.csv

cd ../telco-churn
kaggle datasets download -d blastchar/telco-customer-churn --unzip

cd ../credit-card-fraud
kaggle datasets download -d mlg-ulb/creditcardfraud --unzip
```

Then, per dataset:

```bash
cd benchmarks/<dataset>
python scripts/model.py           # candidate comparison against the baseline
python scripts/evaluate.py        # OOF evaluation + figures
python scripts/explain.py         # permutation importance + SHAP
python scripts/seed_stability.py  # the 5-seed reliability check
```

Figures land in `.last-ds-mile/figures/`; a curated selection is in
[`../showcase/`](../showcase/).

---

## Re-run log

When a skill's guidance changes in a way that would have changed what one of these runs
did, the affected stage is re-run rather than assumed still valid. Re-runs are recorded
here, including the ones that changed nothing — "we checked and it held" is a result.

### 2026-08-07 — `credit-card-fraud`, after the `metric-selection` correction

**Why.** [`metric-selection`](../skills/metric-selection/SKILL.md) had explained ROC-AUC's
failure under imbalance with a wrong mechanism ("dominated by the easy majority-class
true-negative rate"). ROC-AUC is *invariant* to class balance — that is its defining
property — so the stated cause was backwards. `00-frame.md` had quoted that reasoning
when it chose PR-AUC.

**What changed.** `00-frame.md`'s Success Metric section, rewritten against the corrected
skill. The metric choice is unchanged — PR-AUC was and remains right here — but the
justification is now the real one, and it's grounded in this dataset's own arithmetic
rather than a general claim: at 578:1, an FPR of 1.0% is 2,843 false alarms against 492
frauds, capping precision at **14.8% even at perfect recall**. The rewrite also records
PR-AUC's missing caveat (no fixed anchor; its no-skill floor is the base rate) and notes
that the floor legitimately moves from 0.00173 to 0.00167 once `/ds-prep` drops the 1,081
duplicate rows.

**What was re-run, and what it produced.** `model.py`, `evaluate.py`, and
`seed_stability.py` were all re-executed against the full 284,807-row dataset:

| Quantity | Committed | Re-run | |
|---|---|---|---|
| CV PR-AUC | 0.8455 ± 0.0117 | 0.8455 ± 0.0117 | ✅ |
| Baseline PR-AUC | 0.00167 | 0.00167 | ✅ |
| Frozen threshold (max-F2) | 0.4932 | 0.4932 | ✅ |
| Precision / recall at threshold | — | 0.8851 / 0.8309 | TP 393, FP 51, FN 80 |
| Seed stability (5 seeds) | mean 0.8465, std 0.0010 | mean 0.8465, std 0.0010 | ✅ |
| Temporal holdout PR-AUC | — | 0.7725 | day 0 → day 1 |

**Every committed figure and artifact came back byte-identical.** The only file the
re-run modified was the framing narrative. That is the expected outcome — no code and no
metric changed, only a sentence of reasoning — but it is now verified rather than
asserted, and it doubles as a reproducibility check on the whole run.
