---
name: ds-method
description: Shared discipline layer for every Last DS Mile stage — the Red Flags, Common Rationalizations, and Hard Gates that keep data science results honest. Use when running any /ds-* stage, or when asked to skip a baseline, peek at a test set, or ship a model without validation.
---

# ds-method — The Last DS Mile Discipline Layer

## Overview

Every `/ds-*` stage skill in this plugin inherits this shared voice. This is not a
pipeline stage itself — it defines the Red Flags, Rationalizations, and Hard Gates that
every stage cites, so a project can't quietly drift into leakage, inflated metrics, or
unreproducible results.

## When to Use

- Referenced automatically by every stage skill (`ds-frame` through `ds-handoff`) — you
  should not need to invoke it directly.
- Use directly when the user asks "why do I need a baseline," pushes back on a gate, or
  you need to decide whether a stage should stop and ask before proceeding.

## Core Process

1. When a stage skill's process reaches a point covered below, check the relevant table
   instead of inventing new judgment calls ad hoc — this keeps behavior consistent across
   every stage.
2. When a Hard Gate applies, stop and tell the user plainly what's missing and which
   command produces it. Never silently work around a missing gate artifact.
3. When a Red Flag fires, say so out loud before continuing, even if the user seems to
   want to move fast — a flagged result that turns out fine costs one sentence; a
   leaked metric that ships costs the project's credibility.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just peek at the test set once, it's fine" | Once is enough to invalidate it. Every peek is information leaking into your modeling decisions, even implicitly. |
| "The baseline is obviously going to be worse, I'll skip it" | You don't know that until you measure it — and without a baseline you have no idea whether your model's lift is real or noise. |
| "I'll pick the validation strategy after I see how the data looks in modeling" | That's when it becomes a knob you can turn to get the score you want. Validation strategy is decided in `/ds-validate`, before `/ds-model`. |
| "It's just exploratory, I'll clean this up before shipping" | Notebooks nobody can rerun are how "exploratory" becomes what's actually shipped. Hygiene starts now, not at the end. |
| "One aggregate metric is enough to report" | A single leaderboard number hides subgroup failures. `/ds-evaluate` requires slice performance before `/ds-report`. |

## Red Flags

| Red Flag | What it usually means |
|---|---|
| Metric looks too good on the first try (e.g. AUC ≥ 0.98, R² ≥ 0.99) | Suspect target leakage. Don't celebrate — trace every feature back to what would have been known at prediction time. |
| Test set touched during feature engineering or hyperparameter search | Stop. The test set is no longer a valid estimate of generalization. Re-split. |
| Validation metric beats the training metric | Usually a data leak or a broken split (e.g. shuffled time series), not a lucky model. |
| A single feature has near-perfect importance | It's often a proxy for the target or an ID column that leaked in. |
| Model accuracy matches the majority-class rate to 2 decimal places | The model is predicting the majority class. Check class balance and the metric choice. |
| Packaged/served predictions differ from the offline predictions on the same rows | Training/serving skew — a feature is computed differently at serve time than at train time. `/ds-package`'s parity gate exists to catch this before deployment. |

## Hard Gates

- `/ds-model` requires a baseline artifact from `/ds-baseline` and a documented
  validation strategy from `/ds-validate` to exist before modeling. If either is
  missing, stop and run that stage first.
- `/ds-report` requires `/ds-evaluate` to have produced slice/subgroup performance,
  not only an aggregate metric.
- `/ds-handoff` requires the environment to be pinned (lockfile, or `requirements.txt`/
  `environment.yml` with exact versions) before packaging a model for handoff.
- `/ds-package` requires the `/ds-handoff` artifacts (pinned environment, serialized
  model, model card) and refuses to proceed unless the **training/serving parity check**
  passes — the packaged model must reproduce the predictions it produced offline.

Gates are enforced by **warning and stopping to ask**, not by silently refusing or
working around the missing artifact — this plugin's safe-set default is warn, not
block (see the design spec, §5).

## Verification

- [ ] Every stage skill's Common Rationalizations / Red Flags sections either cite this
      skill by name or repeat only the rows relevant to that stage — never a full
      unattributed copy.
- [ ] Any stage with a Hard Gate names the exact prior stage artifact it requires and
      the exact command that produces it.
