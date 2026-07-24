# Worked example — a graded with/without comparison

This is a **committed worked example** so the harness's output has something concrete to
show (and the eval-viewer has something to render) without you having to run the full
loop first. It grades one case per dataset — eval `1`, the vague "build a model and tell
me how well it works" ask — for both arms.

## What is real here, and what is illustrative

Honesty matters more than a clean demo, so the two arms are **not** symmetric in
provenance, and the harness never pretends otherwise:

- **`with_skill` is a REAL run.** It is graded against the actual shipped skilled
  pipeline already in this repo —
  `benchmarks/credit-card-fraud/.last-ds-mile/stages/` and
  `benchmarks/house-prices/.last-ds-mile/stages/`. Every `evidence` string in its
  `grading.json` cites a real stage file and a real number from it. This is exactly what
  best practice #4's "take examples of already existing benchmarks" means: the skilled
  arm is a benchmark that already exists.
- **`without_skill` is a REPRODUCIBLE SCRIPTED baseline.** There is no captured live
  baseline *agent* run in the repo, so `naive_run.py` is a committed script representing
  the documented naive failure mode (the accuracy trap; raw-dollar RMSE + in-sample R²
  on a skewed target). Its numbers are **real and reproducible** — run `python
  naive_run.py` and you get the `Accuracy: 0.9995` / `RMSE: $11,058` that `naive-run.md`
  and the `grading.json` evidence cite. What remains a stand-in is the *agent behaviour*:
  the script embodies "no baseline, reports accuracy as success," but it is a scripted
  representation, not an observed LLM-without-the-plugin.

So the gap shown below is **"a real skilled run vs. a real scripted naive run,"** not a
live agent A/B. A live agent A/B comes from `run_eval.py` + your own executor runs; this
example makes the format legible and demonstrates — with reproducible numbers — the
discipline delta the plugin is built to create.

## The result

| Dataset | Case | with_skill pass^k | without_skill pass^k | gap |
|---|---|---|---|---|
| credit-card-fraud | build a fraud model, tell me how well it works | **1.0** (8/8) | 0.125 (1/8) | **0.875** |
| house-prices | build a pricing model, tell me how well it works | **1.0** (5/5) | 0.20 (1/5) | **0.80** |

The single expectation the naive arm passes in each case is the one about *not*
introducing a leaked feature — the naive run is too simple to leak, but it is also too
simple to establish a baseline, pick a prevalence/scale-appropriate metric, validate
out-of-fold, or state honest lift. That is the plugin's value in one number.

Regenerate from the gradings with:

```bash
python benchmarks/evals/scripts/aggregate.py credit-card-fraud --root example/credit-card-fraud
python benchmarks/evals/scripts/aggregate.py house-prices   --root example/house-prices
```
