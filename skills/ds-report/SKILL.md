---
name: ds-report
description: Turns evaluation and interpretation into a stakeholder-facing narrative — recommendation, assumptions, and limitations stated plainly. Use when someone asks to write up, summarise, or present results. Use when preparing findings for a product team, a manager, or any audience that will act on them.
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
   subgroup performance, not only an aggregate number. If it doesn't, compute the slice
   performance yourself now, say plainly that you did, and continue — never write the
   report around an incomplete evidence base, and never stop the task to send the user
   back to `/ds-evaluate` separately (see `ds-method`'s discipline-gate handling).
2. **If the ask is specifically to confirm the model is good to ship** (not just to
   write it up), delegate a full-pipeline sanity check to the `ds-reviewer` agent
   before concluding — it checks baseline, validation, slice performance, and metric
   choice end to end in one pass, cheaper and more reliably than re-deriving that
   checklist inline.
3. Lead with the decision this informs (from `/ds-frame`), not with model architecture.
4. State the recommendation plainly, then the evidence: baseline comparison, slice
   performance, calibration.
5. **Translate the metric lift into `/ds-frame`'s original cost/business terms, not
   just metric units.** `/ds-frame` required a success metric tied to a real decision
   cost (a false negative costs $Y, a 1-point AUC move is worth $Z); if that
   translation was done once at framing time and never carried forward, the report
   ends up repeating "RMSE improved by 0.04" or "recall is 0.87" with no stated dollar
   or operational impact at the actual chosen operating point — the exact "success
   metric is a pure ML metric with no tie to a business cost" Red Flag `/ds-frame`
   exists to catch, resurfacing here instead. State the lift's real-world size (e.g.
   "the median prediction error corresponds to roughly $X, down from $Y for the
   baseline" or "at the frozen decision threshold, this catches N more true positives
   per 1,000 cases than the baseline, at a cost of M more false alarms").
6. **If the recommendation implies intervening on a feature** — targeting a segment
   for a changed offer, pushing customers toward an option, recommending a policy
   change — rather than just using the model's score to rank or prioritize, check it
   against `causal-vs-predictive` before it ships. A ranking/scoring recommendation
   ("use the score to prioritize outreach") only needs predictive validity, already
   established in `/ds-evaluate`; an intervention recommendation needs a causal
   argument the analysis may not have made.
7. List assumptions and limitations explicitly — what the model does not cover, and
   where it's known to underperform (from the slice table).
8. Write to `.last-ds-mile/stages/09-report.md`: the narrative, the recommendation, the
   cost/business-terms translation, and the assumptions/limitations.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The stakeholders just want the headline number" | The headline number without limitations is how a model gets blamed later for failures it was never evaluated against. |
| "The metric lift speaks for itself, stakeholders can do the cost math" | They usually can't, or won't consistently — an RMSE or AUC delta with no stated dollar/operational size invites the reader to assume it's either huge or negligible, whichever fits their prior. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| The draft report has one metric and no mention of where the model underperforms | This is exactly the condition the Gate Check above exists to catch — go back to `/ds-evaluate`. |
| The report states a metric delta (RMSE, AUC, F1) with no dollar figure, rate, or count tied to the decision from `/ds-frame` | The metric-to-cost translation `/ds-frame` required at framing time never made it into the report — go back and do it here before shipping the narrative. |
| The recommendation tells the reader to change or intervene on a feature (not just use the score to rank/prioritize), based only on that feature's predictive importance from `/ds-explain` | A causal claim has been smuggled into an interventional recommendation the underlying analysis never established — see `causal-vs-predictive`. |

See `ds-method` for the shared Red Flags that apply to every stage.

See `lessons/the-contract-that-wasnt-the-cause.md` for a real example of this exact
failure mode reaching a report before being caught.

## Verification

- [ ] Gate check passed: `.last-ds-mile/stages/07-evaluate.md` includes slice/subgroup
      performance before writing began — computed inline in this run if it wasn't
      already there.
- [ ] Recommendation is explicitly tied to the decision named in `/ds-frame`.
- [ ] The metric lift is translated into `/ds-frame`'s cost/business terms at the
      actual chosen operating point, not left as a bare metric delta.
- [ ] Any recommendation that implies intervening on a feature (not just ranking or
      scoring with it) was checked against `causal-vs-predictive` before it shipped.
- [ ] Assumptions and limitations are stated, not implied or omitted.
- [ ] `.last-ds-mile/stages/09-report.md` written.
