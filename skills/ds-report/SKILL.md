---
name: ds-report
description: Turns evaluation and explanation results into a stakeholder-facing narrative — recommendation, assumptions, and limitations. Hard gate — refuses to proceed without slice/subgroup performance from /ds-evaluate. Use when asked to write up, present, or summarize DS results for a non-technical audience.
---

# ds-report — Communication

## Overview

Converts the evidence from `/ds-evaluate` and `/ds-explain` into a narrative a
stakeholder can act on: a recommendation, its evidence, and its honest limitations.

## When to Use

- After `/ds-evaluate` and `/ds-explain` have both produced their artifacts.
- Whenever asked to write up, present, or summarize DS results for a non-technical
  audience.
- NOT for: packaging the model for reuse (that's `/ds-handoff`) — this stage is about the
  narrative, not the artifact.

## Core Process

1. **Gate check:** confirm `.last-ds-mile/stages/07-evaluate.md` includes slice or
   subgroup performance, not only an aggregate number. If it doesn't, stop and send the
   user back to `/ds-evaluate` rather than writing the report around an incomplete
   evidence base.
2. Lead with the decision this informs (from `/ds-frame`), not with model architecture.
3. State the recommendation plainly, then the evidence: baseline comparison, slice
   performance, calibration.
4. List assumptions and limitations explicitly — what the model does not cover, and
   where it's known to underperform (from the slice table).
5. Write to `.last-ds-mile/stages/09-report.md`: the narrative, the recommendation, and
   the assumptions/limitations.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The stakeholders just want the headline number" | The headline number without limitations is how a model gets blamed later for failures it was never evaluated against. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| The draft report has one metric and no mention of where the model underperforms | This is exactly the condition the Gate Check above exists to catch — go back to `/ds-evaluate`. |

See `ds-method` for the shared Red Flags that apply to every stage.

## Verification

- [ ] Gate check passed: `.last-ds-mile/stages/07-evaluate.md` includes slice/subgroup
      performance, confirmed before writing began.
- [ ] Recommendation is explicitly tied to the decision named in `/ds-frame`.
- [ ] Assumptions and limitations are stated, not implied or omitted.
- [ ] `.last-ds-mile/stages/09-report.md` written.
