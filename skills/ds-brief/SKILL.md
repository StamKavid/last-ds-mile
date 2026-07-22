---
name: ds-brief
description: Translates the /ds-report narrative into a one-page, jargon-free brief for non-technical stakeholders — no metric names, dollar/percentage/count framing only. Use after /ds-report, or when asked to explain DS results to executives, a business audience, or anyone non-technical.
---

# ds-brief — Executive Brief

## Overview

`/ds-report` is written for a technical-enough stakeholder who can sit with RMSE,
AUC, fold spread, and a slice table. Most of the people who actually decide whether
a model ships are not that reader. This stage translates — it never re-derives —
`/ds-report`'s findings into language a non-technical audience can act on without
first learning what a confusion matrix is.

## When to Use

- After `/ds-report` has produced its narrative.
- Whenever asked to explain results to executives, a business audience, a board, or
  any stakeholder without a DS/ML background.
- NOT for: producing new findings or a different recommendation than `/ds-report`
  reached (that would be re-analysis, not translation) — if the technical report's
  conclusion needs to change, go fix `/ds-report` first, then translate the
  corrected version.

## Core Process

1. **Gate check:** confirm `.last-ds-mile/stages/09-report.md` exists. If it
   doesn't, stop and send the user back to `/ds-report` — this stage translates an
   existing narrative, it doesn't build one from raw evaluation results.
2. **Strip every metric name and statistical term** — RMSE, AUC, PR-AUC, F-beta,
   SHAP, p-value, standard deviation, fold, quintile/decile, calibration,
   coefficient, feature importance, confound. If a sentence can't be said without
   one of these words, translate it using `/ds-report`'s own cost-translation
   section (the dollar figure, rate, or count it already computed) — not by
   inventing a new plain-language number that wasn't in the technical report.
3. Structure as five short sections, in this order:
   - **What we built and why** — one or two sentences, tied to the decision named in
     `/ds-frame`. No architecture, no model names as a selling point.
   - **How well it works** — dollars, percentages, or counts only (e.g. "catches 9
     of 10 at-risk customers" or "typical pricing error is about $20,000"), pulled
     directly from `/ds-report`'s cost translation.
   - **Where it's weaker** — named plainly with a real-world reason, not a
     statistical one (e.g. "less reliable for the cheapest homes, which include more
     distressed or family sales" — not "higher RMSE in the Q1 slice").
   - **The recommendation** — stated as plainly as `/ds-report`'s own, e.g. "deploy
     as a suggestion, with a person reviewing the flagged cases."
   - **What happens next** — who owns the decision, and the one or two assumptions
     that would need to hold (from `/ds-report`'s Assumptions section) for the
     recommendation to still be right.
4. **No new claims.** Every sentence must trace back to something already stated in
   `/ds-evaluate`, `/ds-explain`, or `/ds-report`. This stage's job is
   simplification, not additional analysis — if a genuinely new finding surfaces
   while writing this, that belongs back in `/ds-report`, not smuggled into the
   brief alone.
5. **Length discipline:** roughly 300–500 words, one page. A "brief" the length of
   the technical report has failed at the one thing it exists to do.
6. Write to `.last-ds-mile/stages/09b-brief.md` — a companion to `09-report.md`, not
   a renumbering of the pipeline; not every project needs this artifact, so it isn't
   a gate anything downstream depends on.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "A few technical terms add credibility" | The brief's rigor is inherited from `/ds-report`; restating jargon here doesn't add precision, it adds a comprehension barrier for the one audience this document exists for. |
| "Executives can just ask if they don't understand a term" | Usually they won't — they'll either disengage or silently misread the term (mistaking "AUC" for a plain percentage is a common, costly misread). |
| "The technical report already has a plain-English recommendation, this is redundant" | A one-sentence recommendation buried in a report full of metrics still requires reading the metrics to trust it — a genuinely separate, short artifact gets read by people who will never open the full report. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| Any metric name or statistical term appears anywhere in the brief | This stage's translation step was skipped — go back to step 2. |
| A claim in the brief has no matching statement in `/ds-evaluate`, `/ds-explain`, or `/ds-report` | The brief is inventing a finding, not translating one — remove it, or add it to `/ds-report` first with real evidence. |
| The brief is longer than roughly one page | It's restating the technical report rather than distilling it. |

## Verification

- [ ] Gate check passed: `.last-ds-mile/stages/09-report.md` exists and was read
      before writing began.
- [ ] No metric name or statistical term appears anywhere in the brief.
- [ ] Every claim traces back to `/ds-evaluate`, `/ds-explain`, or `/ds-report` —
      nothing new introduced.
- [ ] All five sections present: what/why, how well, where weaker, recommendation,
      what happens next.
- [ ] Roughly 300–500 words — one page, not a restatement.
- [ ] `.last-ds-mile/stages/09b-brief.md` written.
