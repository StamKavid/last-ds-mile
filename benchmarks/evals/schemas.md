# Eval file schemas

The harness adopts the shape of Anthropic's `skill-creator` eval system so results are
portable to its eval-viewer. Four files matter.

## `evals.json` (input — one per dataset)

```jsonc
{
  "skill_name": "last-ds-mile",
  "dataset": { "path": "...", "target_column": "...", "positive_rate": 0.00167 },
  "arms": { "with_skill": "...", "without_skill": "..." },
  "evals": [
    {
      "id": 1,
      "category": "positive | negative-trigger",
      "gate_under_test": "which discipline this probes",
      "prompt": "the task given to the executor agent, verbatim",
      "expected_output": "prose description of a passing result (not graded directly)",
      "files": ["creditcard.csv"],
      "expectations": ["directive assertion 1", "directive assertion 2"]
    }
  ]
}
```

`expectations` are the graded units. Write them as directives about the *outcome*
(practice #2, #5), and include `negative-trigger` cases where a gate should NOT fire
(practice #3).

## `eval_metadata.json` (per run — written by `run_eval.py`)

```jsonc
{ "eval_id": 1, "arm": "with_skill", "trial": 2, "prompt": "...",
  "dataset_path": "...", "created_at": "ISO-8601", "harness": "claude-code" }
```

Isolation (practice #6): every `{eval_id, arm, trial}` gets its own workspace directory
with its own copy of the data — no state bleeds between runs.

## `grading.json` (per run — written by the grader agent)

See `agents/grader.md`. Key fields: `eval_id`, `expectations[] {text, passed, evidence}`,
`summary {passed, failed, total, pass_rate}`, `claims[] {claim, type, verified}`, `notes`.

## `benchmark.json` (output — written by `aggregate.py`)

```jsonc
{
  "metadata": { "skill_name": "...", "trials_per_case": 5, "generated_at": "..." },
  "per_expectation": [
    { "eval_id": 1, "text": "...",
      "with_skill":    { "pass_hat_k": 1.0, "pass_at_k": 1.0, "passes": 5, "trials": 5 },
      "without_skill": { "pass_hat_k": 0.0, "pass_at_k": 0.6, "passes": 3, "trials": 5 },
      "gap": 1.0 }
  ],
  "per_case": [ { "eval_id": 1, "with_skill_pass_rate": 0.88, "without_skill_pass_rate": 0.42 } ],
  "run_summary": { "with_skill": 0.86, "without_skill": 0.48, "gap": 0.38 },
  "notes": "analyst notes"
}
```

`pass_hat_k` (pass^k) = the expectation passed in **all** k trials of that arm
(consistency). `pass_at_k` = it passed in **at least one** trial (peak luck). Practice
#7: report both — a big `pass_at_k` with a low `pass_hat_k` means the behavior is real
but unreliable. `gap` = `with_skill.pass_hat_k − without_skill.pass_hat_k` is the
skill's marginal, reproducible value; a gap near zero on a passing expectation is a
retirement signal (practice #10).
