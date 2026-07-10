---
name: ds-handoff
description: Packages the model and project for reproducibility and handoff — a model card, a pinned environment, and a rerunnable artifact. Hard gate — refuses to proceed without a pinned environment. Use when a model or analysis is ready to be shared, deployed, or handed to another team.
---

# ds-handoff — Reproducibility & Handoff

## Overview

Packages the finished work so someone else can rerun it, trust it, and know its limits —
the last mile the whole plugin is named for.

## When to Use

- The model or analysis is ready to be shared, deployed, or handed to another team.
- After `/ds-report` has produced the stakeholder narrative and limitations.
- NOT for: further tuning or re-evaluation — if the model isn't finished, go back to
  `/ds-model` or `/ds-evaluate` first.

## Core Process

1. **Gate check:** confirm the environment is pinned — a lockfile, or a
   `requirements.txt`/`environment.yml` with exact versions, not bare package names. If
   it isn't pinned, stop and pin it before continuing.
2. Write a model card: what it predicts, a training-data summary, the metric and its
   baseline lift, known limitations (from `/ds-report`), and intended vs. out-of-scope
   use.
3. Confirm the notebook or script reruns cleanly top-to-bottom in a fresh
   kernel/environment before considering the work done.
4. Serialize the model artifact together with its version and the training-data
   hash/date, recorded alongside it.
5. Write to `.last-ds-mile/stages/10-handoff.md`: the model card, the environment pin
   location, the rerun confirmation, and the artifact location.

## Common Rationalizations

See `ds-method` for the shared Rationalizations that apply to every stage, in particular
"it's just exploratory, I'll clean this up before shipping" — the notebook-nobody-could-
rerun failure mode this stage exists to prevent.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| The environment file lists packages with no version numbers | This is exactly the condition the Gate Check above exists to catch — unpinned environments are how "works on my machine" ships. |

See `ds-method` for the shared Red Flags that apply to every stage.

See `lessons/the-notebook-nobody-could-rerun.md` for a real example of a
handoff that looked done but wasn't reproducible.

## Verification

- [ ] Gate check passed: the environment is pinned with exact versions.
- [ ] Model card written, including intended and out-of-scope use.
- [ ] Notebook or script reruns cleanly in a fresh environment.
- [ ] `.last-ds-mile/stages/10-handoff.md` written.
