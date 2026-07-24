# Skill evals — does the plugin actually change the outcome?

The `benchmarks/<dataset>/` runs elsewhere in this folder are *demonstrations*: one
full skilled pipeline, start to finish. They show what good looks like. They do **not**
answer the only question that justifies a skill's existence:

> On the same task, with the same model, does having the plugin produce a materially
> better result than not having it — reliably, not by luck?

This harness answers that. It runs each eval task twice — **with the plugin installed**
and **without it** — grades both blind on the *outcome*, and reports the reproducible
gap.

### What's borrowed from skill-creator, and what's ours

The eval-and-grading contract is taken directly from Anthropic's
[`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
eval system, verified against its source:

- **Faithful to skill-creator:** the `evals.json` schema
  (`{skill_name, evals:[{id, prompt, expected_output, files, expectations}]}`), the
  `grading.json` schema (`{expectations:[{text, passed, evidence}], summary}`), the blind
  grader contract (outcome-not-path, PASS only on genuine completion, claim extraction),
  and the two-arm `with_skill` / `without_skill` design where the baseline is "no skill."
- **Ours, not skill-creator's:** the primary aggregation. skill-creator's `benchmark.json`
  reports `pass_rate` mean ± stddev across N runs; our default `benchmark.json` instead
  reports **`pass^k` / `pass@k` and a per-expectation `gap`** (from best-practice #7 and
  #10, which are not skill-creator concepts), rendered by our own `eval-viewer.html`.
- **Both, so nothing is lost:** `aggregate.py` *also* writes
  **`benchmark.skill-creator.json`** in skill-creator's exact schema (`runs[]` keyed by
  `configuration`, nested `result.pass_rate`, `run_summary.<config>.pass_rate.{mean,stddev}`),
  so the results **do** drop into skill-creator's React eval-viewer. Timing/token fields
  are `null` there — this harness grades committed transcripts, not live executor metrics.
  See `schemas.md` for both shapes.

## Layout

```
benchmarks/evals/
├── README.md            ← this file (methodology)
├── schemas.md           ← the four JSON schemas
├── agents/grader.md     ← the blind grader contract → grading.json
├── scripts/
│   ├── run_eval.py      ← scaffolds isolated per-run workspaces from an evals.json
│   └── aggregate.py     ← grading.json × trials → pass^k, arm gap, benchmark.json
├── credit-card-fraud/
│   ├── evals.json       ← 6 eval cases (4 positive, 2 negative-trigger) — accuracy trap
│   └── results/         ← generated, git-ignored: iteration-N/eval-K/<arm>/trial-T/
├── house-prices/
│   └── evals.json       ← 6 eval cases — target-leakage trap on a skewed regression target
└── example/             ← committed worked example (see example/README.md)
    ├── credit-card-fraud/…  ← eval 1 graded: real skilled run vs. illustrative naive run
    └── house-prices/…
```

Two datasets ship eval sets, chosen for complementary failure modes: **credit-card-fraud**
for the imbalanced-metric (accuracy) trap, **house-prices** for the target-leakage trap
(a neighbourhood-mean-of-`SalePrice` feature) on a skewed regression target. The
`example/` tree is a committed, graded comparison so the output format is legible before
you run anything — read [example/README.md](example/README.md) for exactly what in it is
a real run and what is an illustrative baseline.

## Why credit-card-fraud

It is the cleanest in-scope stress test for the plugin's core value. At 0.167% fraud,
the naive path *looks* excellent and is useless: a model that never predicts fraud is
99.83% accurate. An unskilled run that reports accuracy or ROC-AUC ships a strawman; a
skilled run is forced onto a scored baseline, PR-AUC, an operating threshold, a leakage
audit, and slice performance. The existing skilled pipeline in
`benchmarks/credit-card-fraud/` is the reference for what a passing `with_skill` run
looks like, and its real numbers (majority-class accuracy 99.83%, no-skill PR-AUC =
0.00167, shipped model PR-AUC 0.845) are the ground truth the grader checks claims
against.

## Running it

```bash
# 1. Scaffold isolated workspaces for both arms, 5 trials each.
python benchmarks/evals/scripts/run_eval.py credit-card-fraud/evals.json --trials 5

# 2. For each workspace, run the executor agent on prompt.md, saving its transcript
#    and any outputs into that workspace. The two arms differ ONLY by whether the
#    last-ds-mile plugin is installed — same model, same harness, same prompt.

# 3. Grade each run blind against agents/grader.md → grading.json in each workspace.

# 4. Aggregate into pass^k and the arm gap.
python benchmarks/evals/scripts/aggregate.py credit-card-fraud --iteration 1
```

`run_eval.py` scaffolds and instructs; it does **not** invoke the agent, because that
step is harness-specific (Claude Code vs. Copilot vs. Gemini) and often interactive.
This harness ships the *tasks and the grading*, never invented results — a populated
`benchmark.json` only ever comes from real runs you execute.

## How this follows the 10 skill-eval best practices

| # | Practice | Where it lives here |
|---|---|---|
| 1 | **Start with the skill description** — triggers cause >50% of failures | The `negative-trigger` cases (evals 3–4) are pure trigger tests: they fail if a broad-keyword skill hijacks a plain data question, or fires a slice-performance gate on data with no subgroups. Triggering is graded before any modeling quality is. |
| 2 | **Directives over passive info** | Every `expectation` is a checkable assertion about the result ("A baseline is defined AND scored before the model is presented as good"), not "a baseline is recommended." The grader passes only on genuine completion, not on the words appearing. |
| 3 | **Include negative tests** | 2 of 6 cases are `negative-trigger`: eval 3 (a plain "what columns?" question must NOT trigger framing) and eval 4 (must NOT fabricate demographic slices that don't exist in anonymized data). These stop the plugin from hijacking or over-rigor-ing every request. |
| 4 | **Start small, extend from failures** | Six real prompts, not an exhaustive matrix. Each is a failure mode seen in the wild (the accuracy trap, planted-metric framing, target leakage, test-set peeking). New user-reported bugs become new eval cases — that is the intended growth path, not upfront completeness. |
| 5 | **Grade outcomes, not paths** | `agents/grader.md` grades properties of the result (was a baseline scored? was the leak caught?), explicitly *not* which skill ran, in what order, or which files were read. A run that reaches the honest result by an unexpected route passes. |
| 6 | **Isolate each run** | `run_eval.py` gives every `{eval, arm, trial}` its own workspace with its own `outputs/`. No context bleeds between runs. (The read-only dataset is referenced by path, not copied — isolation is about mutable state, not the shared input.) |
| 7 | **3–5 trials per case; pass^k vs pass@k** | `--trials 5` by default. `aggregate.py` reports **pass^k** (passed in *all* trials — consistency) alongside **pass@k** (passed in *any* — peak luck). A high pass@k with a low pass^k means the behavior is real but unreliable, which is a finding, not a pass. |
| 8 | **Test across harnesses** | `--harness` labels each run's metadata, and results are kept per iteration so Claude Code, Copilot, and Gemini runs stay separable. The grader is deliberately blind to the arm so cross-harness comparison isn't biased. The bike-sharing feedback that motivated this was GPT-via-Copilot — a different harness surfaced different behavior, which is exactly why this axis matters. |
| 9 | **Graduate your evals** | These start as *capability* evals (does the plugin add the discipline at all?). Once an expectation reaches pass^k = 1.0 for `with_skill` across iterations, it graduates into a *regression* guard — re-run it after any skill edit to catch backsliding. The `iteration-N/` structure keeps the history. |
| 10 | **Detect skill retirement** | The `without_skill` arm *is* the retirement probe. Per expectation, `gap = with_skill.pass^k − without_skill.pass^k`. A gap near zero on an expectation both arms pass means the base model already does that work unprompted — that guidance has been absorbed and is a candidate to trim from the skill to save context. |

## Reading the result

The number that matters is the per-expectation **gap**. A big, consistent gap
(`with_skill` passes every trial, `without_skill` fails) is the plugin earning its
context. A near-zero gap is either the base model already being disciplined (retire that
guidance, #10) or the task being too easy to separate the arms (write a harder case, #4).
Overall pass rates are a headline; the per-expectation gaps are the diagnosis.
