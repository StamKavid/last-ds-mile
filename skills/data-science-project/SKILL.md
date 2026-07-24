---
name: data-science-project
description: Use at the very start of a tabular ML or data-science task — building a predictive model, classifying or forecasting a column, or exploring a dataset — when the user has NOT yet entered the Last DS Mile pipeline (no `.last-ds-mile/stages/` yet). Orients them to the guided lifecycle and routes to /ds-frame so framing happens before data or models. Defers to /ds once the pipeline has already started.
---

# data-science-project — The Front Door

## Overview

This is the auto-triggering counterpart to the `/ds` command. It fires when a user
starts a tabular supervised-learning task in plain language ("help me build a churn
model", "predict this column", "let's look at this dataset") without knowing the
pipeline exists. Its whole job is to route them onto the guided rail *before* they —
or the agent — jump straight to EDA or modeling, which is the exact failure mode the
Last DS Mile pipeline exists to prevent.

It does not do any modeling itself. It orients and hands off.

## When to Use

- A tabular ML / data-science task is beginning and no `.last-ds-mile/stages/` directory
  exists yet — the user hasn't entered the pipeline.
- The user describes a predictive goal ("classify", "predict", "forecast a column",
  "score these rows") or an exploratory one ("look at", "explore", "EDA on") for
  row-and-column data.

Do **not** use when:

- `.last-ds-mile/stages/` already exists — the pipeline is underway; defer to `/ds`,
  which routes to the actual next stage.
- The task is text, vision, recommenders, or time-series *forecasting* — outside this
  plugin's scope (see README → Scope).

## Core Process

1. **Check whether the pipeline already started.** Glob `.last-ds-mile/stages/*.md`.
   If any stage file exists, do not re-onboard — run the `/ds` router logic instead
   (print the map, mark stages done/next, route to the first missing stage) and stop.
2. **If nothing exists, orient briefly.** Explain in two sentences that this plugin
   runs DS work through a guided, gated lifecycle (frame → data → explore → prep →
   baseline → validate → model → evaluate → explain → report → handoff) that catches
   target leakage, inflated metrics, and unreproducible results before they ship.
3. **Route to framing, not data.** Recommend `/ds-frame` as the first move — define the
   problem, the target, and what winning looks like before opening the data. Mention
   `/ds` shows the full map at any point.
4. **Do not skip ahead.** Even if the user asked directly for a model or a chart, do not
   start `df.head()` or `model.fit()` here. Framing first is the point.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The user just wants a model — skip the framing and start coding" | Framing is five minutes and decides the target, the metric, and the success bar. Skip it and you can't tell a good model from a lucky one. |
| "I'll just load the CSV and take a quick look first" | Opening data before framing biases what you look for, and `/ds-data` does it properly with a sanitization gate. Frame first. |
| "This user is clearly experienced, they don't need the rail" | The rail's value is the gates (baseline, validation, slices), not the hand-holding. Experienced users leak targets too. |

## Red Flags

| Red Flag | What it usually means |
|---|---|
| Asked to "just build a quick model" with no success criterion stated | No target metric means no way to judge the result. Route to `/ds-frame` before modeling. |
| The first proposed action is `df.head()`, a plot, or `model.fit()` | Data or modeling is being reached for ahead of framing — the pipeline front-loads framing and validation on purpose. |
| A metric or leaderboard target is named before the target column is defined | The goal is being chased before the problem is framed. Frame first. |

## Verification

- [ ] Before any data is loaded or any model is trained, the pipeline was introduced and
      `/ds-frame` recommended — or, if `.last-ds-mile/stages/` already existed, the user
      was routed to their real next stage via the `/ds` logic instead of re-onboarded.
- [ ] The user was not silently dropped into EDA or modeling ahead of framing.
