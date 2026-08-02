---
name: ds-method
description: Holds the shared discipline every stage of this pipeline cites — the Red Flags, the Common Rationalizations, and the Hard Gates. Use when someone pushes back on a gate, asks why a baseline is needed, or wants to peek at the test set just once. Use when deciding whether a stage should stop and ask or produce the missing work itself.
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
2. When a **discipline gate** applies and its artifact is missing, produce it inline —
   run the prior stage's work yourself, in the same turn, and say plainly what you
   produced and why. Never silently work around a missing gate artifact, and never end
   the turn asking the user to go run a separate command first: the gate is satisfied
   by doing the work, not by requesting permission to do it.
3. When a **safety gate** applies (see below), stop and ask before proceeding — these
   are the cases where continuing unilaterally could be irreversible or externally
   visible.
4. Before running a stage's full process, climb the **stage ladder**: (a) does that
   stage's artifact already exist? if so, reuse it, don't redo it. (b) does this
   request actually need it, or can the ask be answered without it (see `ds-method`'s
   guard against escalating a plain question)? (c) can it be satisfied in a couple of
   lines in the run's notes, rather than a full stage write-up? Stop at the first rung
   that resolves it. If you track progress with a todo list, keep **one list for the
   whole run**, not a fresh create/update pair per stage — a dozen-plus todo-tool calls
   for a single request is a sign the ladder above wasn't applied.
5. **Pick the artifact mode once, at the start, and say which you picked:**
   - **Express** (default for a single-shot request answered in one session — "build a
     model for X and tell me how it does"): write **one** `.last-ds-mile/run.md`
     carrying every stage's output — framing, baseline, validation choice, model
     comparison, evaluation/slices — as sections in that one file, not a dozen separate
     `stages/*.md` files. The gates and their evidence still all have to be there; only
     the file layout is consolidated.
   - **Full per-stage** (a genuine multi-session project, or the user asks to run a
     specific `/ds-*` stage on its own): each stage writes its own
     `.last-ds-mile/stages/NN-name.md` as described in that stage's own Core Process —
     this is what makes stages resumable and reviewable independently across sessions.
   - Once a project has `.last-ds-mile/stages/` files, stay in full per-stage mode for
     consistency; don't switch an in-progress project to express mid-way.
6. When a Red Flag fires, say so out loud before continuing, even if the user seems to
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
| A model is serving with no online comparison against its baseline | Degradation is invisible — you can't tell if the deployed model still beats the dumb baseline it was justified against. `/ds-deploy` requires monitoring before full traffic. |

## Hard Gates

Every gate below still requires the same artifact it always did — nothing here makes a
gate optional. What differs is the remedy when the artifact is missing: **discipline
gates self-heal** (produce the artifact inline and continue); **safety gates stop and
ask** (the action is irreversible or externally visible, so continuing unilaterally
isn't yours to decide).

**Discipline gates — produce the missing artifact inline, state that you did, continue:**

- `/ds-model` requires a baseline artifact from `/ds-baseline` and a documented
  validation strategy from `/ds-validate` to exist before modeling. If either is
  missing, run that stage's work yourself in the same turn, then model.
- `/ds-report` requires `/ds-evaluate` to have produced slice/subgroup performance,
  not only an aggregate metric. If it's missing, compute it before reporting.
- `/ds-handoff` requires the environment to be pinned (lockfile, or `requirements.txt`/
  `environment.yml` with exact versions) before packaging a model for handoff. If it's
  missing, pin it, then hand off.

**Safety gates — stop and ask before proceeding:**

- `/ds-package` requires the `/ds-handoff` artifacts (pinned environment, serialized
  model, model card) and refuses to proceed unless the **training/serving parity check**
  passes — the packaged model must reproduce the predictions it produced offline. A
  failing parity check is a correctness problem the user needs to see, not one to paper
  over inline.
- `/ds-deploy` requires the `/ds-package` artifacts (a parity-verified image and an
  inference contract) and refuses a full-traffic deploy unless a **monitoring hook, a
  drift hook, and a rollback pointer** all exist. Any push to a remote/registry/cloud
  target stops and asks — the plugin never pushes to production on its own.

Discipline gates are enforced by doing the missing work and saying so, never by
silently skipping the artifact and never by ending the turn to ask the user to go
produce it themselves. Safety gates keep the warn-don't-block posture from the design
spec (§5): the plugin flags what's missing and stops, but never silently refuses or
works around it either.

## Verification

- [ ] Every stage skill's Common Rationalizations / Red Flags sections either cite this
      skill by name or repeat only the rows relevant to that stage — never a full
      unattributed copy.
- [ ] Any stage with a Hard Gate names the exact prior stage artifact it requires and
      the exact command that produces it.
