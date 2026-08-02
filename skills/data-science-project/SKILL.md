---
name: data-science-project
description: Carries a tabular machine-learning request from a plain-language ask all the way to a scored model and an honest verdict, in one turn. Use when the user says build a model, train a classifier, classify or predict or forecast a column, or detect something in a CSV, table, or spreadsheet. Use when someone wants to look at a dataset and see whether an outcome can be classified or predicted from it. Use when someone asks how well a model works, whether a result is good enough, or whether a model is ready to ship. Use when a data-science task is starting and no `.last-ds-mile/` work exists yet.
---

# data-science-project — The Front Door

## Overview

This is the auto-triggering counterpart to the `/ds` command. It fires when a user
starts a tabular supervised-learning task in plain language ("help me build a churn
model", "predict this column", "let's look at this dataset") without knowing the
pipeline exists.

Its job is to make sure framing, an honest baseline, and a leakage-safe validation
strategy happen **before** the headline model number is reported — without stopping
the run to ask permission first. Frame inline, then keep going: the gates (baseline,
validation, slices) are what this plugin is for, not a pause for orientation.

## When to Use

- A tabular ML / data-science task is beginning and no `.last-ds-mile/stages/` directory
  exists yet — the user hasn't entered the pipeline.
- The user describes a predictive goal ("classify", "predict", "forecast a column",
  "score these rows") or an exploratory one ("look at", "explore", "EDA on") for
  row-and-column data.

Do **not** use when:

- `.last-ds-mile/stages/` already exists — the pipeline is underway; defer to `/ds`,
  which routes to the actual next stage.
- The user asked a direct factual question about the data (columns, row count, dtypes)
  with no modeling or evaluation ask attached — just answer it. See `ds-method`'s guard
  against escalating a plain question into a framing exercise.
- The task is text, vision, recommenders, or time-series *forecasting* — outside this
  plugin's scope (see README → Scope).

## Core Process

1. **Check whether the pipeline already started.** Glob `.last-ds-mile/stages/*.md`.
   If any stage file exists, do not re-onboard — run the `/ds` router logic instead
   (print the map, mark stages done/next, route to the first missing stage) and stop.
2. **Frame in-line, in one or two sentences, then move on.** State the target, the
   decision it feeds, and the success metric as your own best read of the request — do
   not ask the user to confirm before proceeding. Only ask a question here if the
   answer would change which column is the target or invalidate the whole run; note
   assumptions instead of pausing on anything else.
3. **Carry the request through the pipeline in this same turn**, applying each stage's
   gate as you reach it (honest baseline, leakage-safe validation, slice performance)
   rather than stopping to hand off. Pick an artifact mode per `ds-method` — express
   (one `.last-ds-mile/run.md` for a single-shot ask, the default here) or full
   per-stage `.last-ds-mile/stages/*.md` files (a genuine multi-session project) — and
   say which you picked. Either way, the artifact is a record of what you did, not a
   checkpoint to wait at.
4. **Never end the turn asking permission to begin.** A request to build or evaluate a
   model is carried through to a model, a scored baseline, and a verdict — not a
   pipeline map and a question. If you are missing a Hard Gate artifact `ds-method`
   requires, produce it inline (see `ds-method`'s discipline-gate handling) and say so;
   don't stop and ask the user to go run a separate command first.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I should explain the pipeline and ask where to start before doing anything" | The user already asked for the outcome. Frame it yourself in one line and go — asking first is the failure mode this skill exists to avoid, not a safety net. |
| "No `.last-ds-mile/stages/` exist, so I should stop here and let the user choose a starting stage" | Absence of prior stages means start at `/ds-frame` and continue, not stop. Only `/ds-model`, `/ds-report`, and `/ds-handoff`'s Hard Gates are worth stopping for — and even those get produced inline, not deferred to the user. |
| "This user is clearly experienced, they don't need the rail" | The rail's value is the gates (baseline, validation, slices), not the hand-holding. Experienced users leak targets too. |

## Red Flags

| Red Flag | What it usually means |
|---|---|
| The run ends with a question about which stage to start at, instead of a result | The framing-and-handoff instinct fired instead of framing-and-continuing. Go back and do the work. |
| Asked to "just build a quick model" with no success criterion stated | No target metric means no way to judge the result. Frame it in one line yourself, then proceed. |
| A metric or leaderboard target is named before the target column is defined | The goal is being chased before the problem is framed. State the framing, then go. |

## Verification

- [ ] The run produced a result — a scored baseline, a model, or an evaluation verdict
      — not just a pipeline map and a question about where to start.
- [ ] Framing (target, decision, metric) was stated in-line, not requested from the
      user as a precondition to starting.
- [ ] Every Hard Gate the request touched (baseline, validation, slice performance,
      pinned environment) was either satisfied or produced inline before the final
      claim — never silently skipped, and never left for the user to go run separately.
