---
name: notebook-hygiene
description: Keeps notebooks reproducible and reviewable — safe to rerun top-to-bottom, safe to read out of execution order. Use when finishing exploratory work that will be shared, reviewed, or handed off, or when a notebook's cells have been run out of order and its current state is no longer trustworthy.
---

# notebook-hygiene

## Overview

A notebook is only as trustworthy as its ability to be rerun from a blank kernel and
produce the same result — this skill is the concrete checklist for that property,
which is otherwise easy to lose one out-of-order cell execution at a time.

## When to Use

- Before considering exploratory work "done" — especially before `/ds-handoff`.
- A notebook has been edited/re-run out of order and you're not sure its current
  displayed output matches what the code would actually produce.
- NOT for: environment pinning itself (that's `/ds-handoff`'s Gate Check) — this
  skill is about the notebook's own internal consistency, handoff is about the
  surrounding environment.

## Core Process

1. Before finishing a session, do a **Restart & Run All** (or the script
   equivalent: run the whole file fresh, top to bottom, in a new process) and
   confirm it completes without error and without needing manual intervention.
2. Check that cell execution order in the saved notebook matches top-to-bottom
   order — a notebook where cell 12 was run before cell 5 can display results that
   don't match a fresh run, even though it "looks fine" right now.
3. Set random seeds explicitly wherever randomness is used (splits, model init,
   resampling) — an unset seed makes "restart and run all" produce different
   numbers each time, which looks like a reproducibility failure even when the code
   is correct.
4. Remove or clearly mark any manual/interactive step (a value pasted in by hand, a
   file path typed once and never reused) that a rerun would silently skip.

## Techniques/Patterns

| Hygiene issue | How it shows up | Fix |
|---|---|---|
| Out-of-order execution | Cell numbers in the saved notebook aren't sequential top to bottom | Restart & Run All before saving; if a cell must run early for exploration, don't leave the notebook in that state as "final" |
| Hidden global state | A later cell depends on a variable set by a cell above it that's since been deleted or edited | Restart & Run All will catch this immediately — that's exactly why it's step 1, not a nice-to-have |
| Unset random seeds | Rerunning produces different train/test splits, different model coefficients, different plots | Set `random_state`/`np.random.seed`/`torch.manual_seed` explicitly, once, near the top |
| Notebook-as-production-code | A notebook with real business logic that nobody can run non-interactively | For anything beyond exploration, extract the logic into a plain `.py` module/script the notebook imports and calls — the notebook becomes a thin driver, not the source of truth |

## Common Rationalizations

See `ds-method` for the shared Rationalizations that apply to every stage, in
particular "it's just exploratory, I'll clean this up before shipping" — this skill
exists specifically to make "cleaning it up" a concrete, checkable action instead of
a vague intention.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| The notebook has never been run via Restart & Run All since its last substantive edit | Its currently-displayed output cannot be trusted to match what the code actually produces |

See `ds-method`'s Red Flags for the broader "notebook nobody could rerun" failure
mode this skill directly targets.

See `lessons/the-notebook-nobody-could-rerun.md` for a real example of this
exact failure mode.

## Verification

- [ ] Restart & Run All (or fresh-process script run) completed without error
      immediately before considering the work done.
- [ ] All randomness sources have an explicit, recorded seed.
- [ ] No cell depends on a manual/interactive step that a fresh run would silently
      miss.
