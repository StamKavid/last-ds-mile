---
name: ds-iterate
description: Reads /ds-evaluate's error analysis and slice table, categorizes what's actually wrong (bias, variance, a specific slice, a leakage suspicion, or a data problem), and routes back to the exact prior stage that fixes it — closing the loop the pipeline would otherwise run once and stop. Use after /ds-evaluate whenever the result isn't good enough to ship, or when deciding whether to iterate again versus proceed to /ds-explain.
---

# ds-iterate — Diagnose and Route Back

## Overview

`/ds-frame` through `/ds-handoff` reads like a straight line, but real modeling work is
a loop: evaluate, find what's wrong, fix the specific thing, re-evaluate. Without an
explicit stage for that loop, an agent following this pipeline literally will run one
pass end-to-end and call it done, even when `/ds-evaluate`'s own error analysis is
pointing at a fixable weakness. This stage is the diagnosis-and-routing step that turns
one pass into a real iteration.

## When to Use

- Immediately after `/ds-evaluate`, before deciding whether to proceed to
  `/ds-explain` or go back for another pass.
- The aggregate metric is acceptable but a slice, an error-analysis pattern, or a
  calibration issue from `/ds-evaluate` suggests a fixable, specific weakness.
- NOT for: re-running the exact same modeling step hoping for a better random draw
  (that's not iteration, that's noise-chasing — see `uncertainty-quantification` for
  whether a gap is even real) — this stage requires a *specific, named* fix.

## Core Process

1. Read `.last-ds-mile/stages/07-evaluate.md` in full: the slice table, the
   calibration check, and the worst-mispredictions pattern. Do not skip straight to a
   verdict — the diagnosis has to come from what's actually written there.
2. Categorize the gap using the table below. Pick the category the evidence actually
   supports, not the one that's easiest to act on.
3. If the diagnosis points to bias (systematic underperformance everywhere, including
   on training data) or variance (train much better than validation), check for a
   learning-curve signal before deciding the fix: does more data help (variance), or
   does a more expressive model/feature set help (bias)? State which, briefly.
4. Route back to the *one* prior stage that addresses the diagnosed cause — not a
   generic "try again." Re-run only that stage; don't restart the whole pipeline.
5. Cap iteration: after 3 loops on the same problem without the diagnosed issue
   resolving, stop looping and say so plainly — report the unresolved gap as a known
   limitation for `/ds-report` rather than iterating indefinitely chasing a better
   number.
6. Append one entry to `.last-ds-mile/stages/07-iterate-log.md` per loop: the
   diagnosis, the stage routed back to, what changed, and the resulting metric versus
   the previous loop's — so the loop's history is auditable, not silently overwritten.

## Techniques/Patterns — diagnosis routing table

| Evidence from `/ds-evaluate` | Diagnosis | Route back to |
|---|---|---|
| One or two slices are much worse than the aggregate; error analysis shows a pattern concentrated there | Slice-specific weakness | `/ds-prep` — add or fix a feature that would help that slice specifically |
| Aggregate metric itself is unsatisfactory, and it's already close to (or worse than) the baseline everywhere | High bias — the model/feature set is too weak | `/ds-prep` (more/better features) or `/ds-model` (a more expressive model class) |
| Validation metric much worse than the training metric, uniformly across slices | High variance — overfit | `/ds-model` (regularization, simpler model, more data) — re-check `/ds-validate`'s split is not itself the cause first (see `validation-strategy`'s Red Flags) |
| A feature's importance or a slice's near-perfect performance looks suspicious | Leakage suspicion | `target-leakage-detection`, then `/ds-prep` if confirmed |
| CV score looked fine but a held-out/temporal check underperformed | Distribution shift | `distribution-shift`, then `/ds-validate` if the split itself needs to change |
| The evidence is solid and no specific fixable weakness stands out | No further iteration warranted | Proceed to `/ds-explain` — say so explicitly rather than looping without a hypothesis |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The aggregate number is good enough, I don't need to look at the slice table again" | That's exactly what `/ds-evaluate` produced the slice table to prevent skipping — if a slice weakness is sitting there documented, ignoring it here just delays the same finding to `/ds-report`, where it's more expensive to fix. |
| "I'll just retrain with a different seed and see if the number improves" | That's not iteration, it's hoping for favorable noise — see `uncertainty-quantification`. A real iteration changes a feature, a model class, or the data based on a specific diagnosis. |
| "We've already looped twice, let's just ship what we have" | Fine, but say that explicitly as a stated limitation in `/ds-report` — don't quietly stop iterating and report the last number as if it were final and clean. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| Looping more than 3 times on the same diagnosed issue with no improvement | The diagnosis is probably wrong, or the fix needs more than another `/ds-prep`/`/ds-model` pass — stop and reconsider the framing (`/ds-frame`) or flag it as a real limitation instead of continuing to loop. |
| A loop's "fix" is retrying the same stage with no change other than a random seed | Not a real iteration — see the noise-chasing rationalization above. |

See `ds-method`'s Red Flags for the shared list.

## Verification

- [ ] Diagnosis is drawn from `.last-ds-mile/stages/07-evaluate.md`'s actual slice
      table and error analysis, not asserted without re-reading it.
- [ ] Exactly one prior stage was routed back to, matching the diagnosis table, not a
      full pipeline restart.
- [ ] Each loop is appended to `.last-ds-mile/stages/07-iterate-log.md`, not
      overwritten.
- [ ] If iteration stopped without resolving the diagnosed issue, that's stated as a
      limitation for `/ds-report`, not silently dropped.
